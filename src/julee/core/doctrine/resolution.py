"""Resolving parsed class names to the classes they name.

Whether a class is a pydantic DTO cannot be read off its bases in the
AST: a local class called ``BaseModel``, an aliased import and a base
from an unparsed package all read the same as pydantic's.

So this imports the target's modules and asks Python. The rules stay
pure functions over the verdicts.
"""

import ast
import collections.abc
import dataclasses
import datetime
import decimal
import enum
import importlib
import inspect
import pathlib
import typing
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from pydantic import BaseModel
from pydantic.dataclasses import is_pydantic_dataclass

from julee.core.doctrine_constants import ENTITIES_PATH, USE_CASES_PATH

__all__ = [
    "PRIMITIVES",
    "package_of",
    "Verdict",
    "dto_verdicts",
    "entity_verdicts",
    "module_name_for",
    "port_verdicts",
]


@dataclass(frozen=True)
class Verdict:
    """What resolving one class name found.

    ``reason`` is None when the class complies, and otherwise says why
    not, in words an objection can use directly.
    """

    bounded_context: str
    name: str
    reason: str | None


def module_name_for(path: Path) -> str | None:
    """The dotted module name a file is importable as.

    Walks up while there is an ``__init__.py``. Returns None for a
    file in no package.

    Args:
        path: Path to a .py file

    Returns:
        The dotted name, or None
    """
    if (parent := path.parent) is None or not (parent / "__init__.py").exists():
        return None

    if path.name == "__init__.py":
        # A package's __init__ is imported by the package's own name.
        parts: list[str] = []
        directory = parent
    else:
        parts = [path.stem]
        directory = parent
    while (directory / "__init__.py").exists():
        parts.append(directory.name)
        directory = directory.parent
    return ".".join(reversed(parts))


def package_of(path: Path) -> str:
    """The package a file's relative imports resolve against.

    For ``a/b/c.py`` that is ``a.b``; for ``a/b/__init__.py`` it is
    ``a.b`` as well, since a package's init sits in the package rather
    than beside it.

    Args:
        path: Path to a .py file

    Returns:
        The dotted package path, empty if the file is in no package
    """
    name = module_name_for(path) or ""
    if path.name == "__init__.py":
        return name
    return name.rsplit(".", 1)[0] if "." in name else ""


def _files_under(directory: Path) -> list[Path]:
    """Every module in a layer directory, tests excluded."""
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.rglob("*.py")
        if "tests" not in path.parts and path.name != "__init__.py"
    )


def _import_layer(
    slug: str, context_path: Path, layer: tuple[str, ...]
) -> tuple[list[ModuleType], list[Verdict]]:
    """Import what a context keeps in one layer directory.

    A file that will not parse or will not import gets a verdict of
    its own. Nothing else reports one, because such a file contributes
    no classes for a rule to look at.

    Args:
        slug: The bounded context slug
        context_path: Path to the bounded context
        layer: Path segments of the directory, e.g. ("usecases",)

    Returns:
        The modules that imported, and a verdict per file that did not
    """
    directory = context_path
    for segment in layer:
        directory = directory / segment

    modules: list[ModuleType] = []
    failures: list[Verdict] = []

    for path in _files_under(directory):
        relative = path.relative_to(context_path)
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError) as error:
            failures.append(
                Verdict(slug, str(relative), f"it does not parse ({error})")
            )
            continue

        name = module_name_for(path)
        if name is None:
            failures.append(
                Verdict(
                    slug, str(relative), "it is in no package, so nothing imports it"
                )
            )
            continue
        try:
            modules.append(importlib.import_module(name))
        except Exception as error:  # noqa: BLE001 - any import failure is a verdict
            failures.append(
                Verdict(slug, str(relative), f"it does not import ({error!r})")
            )

    return modules, failures


def _not_a_dto(obj: object) -> str | None:
    """Why an object is not a DTO, or None if it is one.

    A DTO is a BaseModel. A pydantic dataclass validates too but is
    refused, because it also satisfies the domain's frozen-dataclass
    rule and so cannot say which ring it belongs to.

    Args:
        obj: Whatever the name resolved to

    Returns:
        A clause for the objection, or None
    """
    if not isinstance(obj, type):
        return f"{obj!r} is not a class"
    if is_pydantic_dataclass(obj):
        return (
            "it is a pydantic dataclass. A DTO is a BaseModel; a pydantic "
            "dataclass reads as a plain dataclass everywhere else and so "
            "belongs to neither ring"
        )
    if not issubclass(obj, BaseModel):
        return f"{obj!r} is not a pydantic BaseModel"
    return None


IMMUTABLE_BUILTINS = (bytes, float, frozenset, int, str, tuple)
"""Builtins a value object may subclass and still be immutable.

``Slug``, ``Name`` and ``ContentMultihash`` are str subclasses. They
carry a rule about their own text and nothing can change them after
construction, which is what the domain ring asks for; being a
dataclass is not the point, immutability is.
"""


def _not_a_domain_class(obj: object) -> str | None:
    """Why a class does not belong in the domain ring, or None if it does.

    A domain class is a frozen stdlib dataclass, an enum, or a
    subclass of an immutable builtin. Pydantic is refused in both its
    forms: a model carries a serialisation library into the ring, and
    a dataclass of pydantic's reads as a plain one everywhere while
    importing pydantic all the same.

    Args:
        obj: Whatever the name resolved to

    Returns:
        A clause for the objection, or None
    """
    if not isinstance(obj, type):
        return None

    if issubclass(obj, enum.Enum):
        return None
    if issubclass(obj, IMMUTABLE_BUILTINS):
        return None

    if is_pydantic_dataclass(obj):
        return (
            "it is a pydantic dataclass. The domain uses stdlib "
            "dataclasses; this one reads as one and imports pydantic"
        )
    if issubclass(obj, BaseModel):
        return "it is a pydantic model. A domain class is a frozen dataclass"

    if dataclasses.is_dataclass(obj):
        params = getattr(obj, "__dataclass_params__", None)
        if params is not None and params.frozen:
            return None
        return "it is a dataclass that is not frozen"

    return "it is not a frozen dataclass, an enum or an immutable value"


def _verdicts(
    slug: str,
    context_path: Path,
    layer: tuple[str, ...],
    names: list[str],
    judge: Callable[[object], str | None],
) -> list[Verdict]:
    """Resolve names against one layer's modules and judge each.

    A name is looked for as an attribute of any module in the layer,
    so it is found whether defined there or imported into it.

    A name that resolves to nothing gets a verdict rather than a pass.

    Args:
        slug: The bounded context slug
        context_path: Path to the bounded context
        layer: Path segments of the layer directory
        names: The class names the parser found
        judge: What to ask of each resolved class

    Returns:
        One verdict per name, plus one per file that would not import
    """
    modules, verdicts = _import_layer(slug, context_path, layer)

    for name in names:
        found = next(
            (getattr(module, name) for module in modules if hasattr(module, name)),
            None,
        )
        if found is None:
            verdicts.append(
                Verdict(slug, name, "doctrine could not resolve it to a class")
            )
        else:
            verdicts.append(Verdict(slug, name, judge(found)))

    return verdicts


def entity_verdicts(slug: str, context_path: Path, names: list[str]) -> list[Verdict]:
    """Resolve entity names against the context's domain models.

    Args:
        slug: The bounded context slug
        context_path: Path to the bounded context
        names: The entity class names the parser found

    Returns:
        One verdict per name, plus one per file that would not import
    """
    return _verdicts(slug, context_path, ENTITIES_PATH, names, _not_a_domain_class)


def dto_verdicts(slug: str, context_path: Path, names: list[str]) -> list[Verdict]:
    """Resolve DTO names against the context's use case modules.

    Args:
        slug: The bounded context slug
        context_path: Path to the bounded context
        names: The Request or Response class names the parser found

    Returns:
        One verdict per name, plus one per file that would not import
    """
    return _verdicts(slug, context_path, USE_CASES_PATH, names, _not_a_dto)


PRIMITIVES = frozenset(
    {
        bool,
        bytes,
        complex,
        float,
        int,
        str,
        type(None),
        datetime.date,
        datetime.datetime,
        datetime.time,
        datetime.timedelta,
        decimal.Decimal,
        pathlib.PurePath,
        pathlib.Path,
        uuid.UUID,
    }
)
"""Types a driven port may name besides the domain's own.

Stdlib values with an obvious serialised form. A port dealing in these
is not leaking a representation into the domain.
"""


def _foreign(annotation: object) -> list[str]:
    """What a type expression names that a driven port may not.

    Walks the expression, so ``tuple[Story, ...]`` is judged by Story
    and ``dict[str, Any]`` by Any.

    Args:
        annotation: A resolved annotation, from get_type_hints

    Returns:
        One description per offending type, empty if all are allowed
    """
    if annotation is typing.Any:
        return ["Any"]
    if annotation is Ellipsis:
        return []

    if (origin := typing.get_origin(annotation)) is not None:
        arguments = typing.get_args(annotation)
        if origin is collections.abc.Callable:
            # (args, return) — the args arrive as a list, or Ellipsis.
            arguments = tuple(
                argument
                for group in arguments
                for argument in (group if isinstance(group, list) else [group])
            )
        return [name for argument in arguments for name in _foreign(argument)]

    if isinstance(annotation, typing.TypeVar):
        if annotation.__bound__ is None and not annotation.__constraints__:
            return [f"{annotation} (an unbounded type variable)"]
        if annotation.__bound__ is not None:
            return _foreign(annotation.__bound__)
        return [
            name
            for constraint in annotation.__constraints__
            for name in _foreign(constraint)
        ]

    if annotation in PRIMITIVES:
        return []

    if isinstance(annotation, type):
        if issubclass(annotation, enum.Enum):
            return []
        if is_pydantic_dataclass(annotation):
            return [f"{annotation.__name__} (a pydantic dataclass)"]
        if issubclass(annotation, BaseModel):
            return [f"{annotation.__name__} (a pydantic model)"]
        if dataclasses.is_dataclass(annotation):
            # __dataclass_params__ is not in the stub's DataclassInstance,
            # and is the only place frozen= is recorded at runtime.
            params = getattr(annotation, "__dataclass_params__", None)
            if params is not None and params.frozen:
                return []
            return [f"{annotation.__name__} (a dataclass that is not frozen)"]
        return [f"{annotation.__name__} (not a frozen dataclass)"]

    return [f"{annotation!r}"]


def _method_offences(protocol: type, method: str, function: object) -> list[str]:
    """What one method of a protocol names that it may not.

    A parameter with no annotation and a missing return type are
    offences of their own: an unstated type is not a permitted one.

    Args:
        protocol: The port protocol the method belongs to
        method: The method's name
        function: The function object

    Returns:
        One sentence per offence
    """
    try:
        hints = typing.get_type_hints(function)
    except Exception as error:  # noqa: BLE001 - any resolution failure is an offence
        return [f"{method}(): its annotations do not resolve ({error!r})"]

    offences = []
    signature = inspect.signature(function)  # type: ignore[arg-type]
    for name, parameter in signature.parameters.items():
        if name in {"self", "cls"} or parameter.kind is parameter.VAR_KEYWORD:
            continue
        if parameter.annotation is inspect.Parameter.empty:
            offences.append(f"{method}({name}): no type is declared")
            continue
        offences.extend(
            f"{method}({name}): {found}" for found in _foreign(hints.get(name))
        )

    if "return" not in hints:
        offences.append(f"{method}(): no return type is declared")
    else:
        offences.extend(
            f"{method}() returns {found}" for found in _foreign(hints["return"])
        )

    return offences


def _is_ours(function: object, protocol: type) -> bool:
    """Whether a method comes from the solution's code or from julee.

    A port inheriting from a third-party class would otherwise have
    that library's whole API judged as part of its surface.
    """
    module = getattr(function, "__module__", "") or ""
    package = (protocol.__module__ or "").split(".")[0]
    return module.split(".")[0] in {package, "julee"}


def _declared_methods(protocol: type) -> dict[str, object]:
    """The methods a protocol offers, its own and those it inherits.

    Inherited ones count: a repository that declares nothing and gets
    its CRUD from a base still offers those methods to a use case.

    Args:
        protocol: The port protocol to read

    Returns:
        Method name to function
    """
    ignored = set(dir(typing.Protocol)) | set(dir(object))
    return {
        name: member
        for name, member in inspect.getmembers(protocol, inspect.isfunction)
        if not name.startswith("_")
        and name not in ignored
        and _is_ours(member, protocol)
    }


def port_verdicts(
    slug: str, context_path: Path, names_by_layer: dict[tuple[str, ...], list[str]]
) -> list[Verdict]:
    """Resolve driven port protocols and judge their signatures.

    Args:
        slug: The bounded context slug
        context_path: Path to the bounded context
        names_by_layer: Protocol names, by the layer directory holding them

    Returns:
        One verdict per offence, plus one per file that would not import
    """
    verdicts: list[Verdict] = []

    for layer, names in names_by_layer.items():
        modules, failures = _import_layer(slug, context_path, layer)
        verdicts.extend(failures)

        for name in names:
            found = next(
                (getattr(module, name) for module in modules if hasattr(module, name)),
                None,
            )
            if not isinstance(found, type):
                verdicts.append(
                    Verdict(slug, name, "doctrine could not resolve it to a class")
                )
                continue
            for method, function in _declared_methods(found).items():
                verdicts.extend(
                    Verdict(slug, name, offence)
                    for offence in _method_offences(found, method, function)
                )

    return verdicts
