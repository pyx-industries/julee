"""Resolving parsed DTO names to the classes they name.

Reading bases out of the AST cannot answer whether a class is a
pydantic DTO. A local class called ``BaseModel``, a base imported from
a package doctrine does not parse, an alias, a request defined outside
``usecases/`` and imported back in — each of them reads as compliant
and none of them is.

So this imports the target's use case modules and asks Python. The
rules stay pure functions over the verdicts; the importing is here.
"""

import ast
import importlib
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from pydantic import BaseModel
from pydantic.dataclasses import is_pydantic_dataclass

__all__ = ["Verdict", "dto_verdicts", "module_name_for"]


@dataclass(frozen=True)
class Verdict:
    """What resolving one DTO name found.

    ``reason`` is None when the class is a pydantic DTO, and otherwise
    says why it is not, in words that go straight into an objection.
    """

    bounded_context: str
    name: str
    reason: str | None


def module_name_for(path: Path) -> str | None:
    """The dotted module name a file is importable as.

    Walks up while there is an ``__init__.py``, which is what makes the
    directory a package. Returns None for a file in no package, since
    there is no name to import it by.

    Args:
        path: Path to a .py file

    Returns:
        The dotted name, or None
    """
    if (parent := path.parent) is None or not (parent / "__init__.py").exists():
        return None

    parts = [path.stem]
    directory = parent
    while (directory / "__init__.py").exists():
        parts.append(directory.name)
        directory = directory.parent
    return ".".join(reversed(parts))


def _usecase_files(context_path: Path) -> list[Path]:
    """Every use case file of a context, tests excluded."""
    usecases = context_path / "usecases"
    if not usecases.is_dir():
        return []
    return sorted(
        path
        for path in usecases.rglob("*.py")
        if "tests" not in path.parts and path.name != "__init__.py"
    )


def _import_usecase_modules(
    slug: str, context_path: Path
) -> tuple[list[ModuleType], list[Verdict]]:
    """Import what a context keeps under usecases/.

    A file that will not parse or will not import is a verdict of its
    own. Nothing else reports one: a file the AST parser cannot read
    contributes no classes, so every rule passes over it in silence,
    and a request in it is never checked by anything.

    Args:
        slug: The bounded context slug
        context_path: Path to the bounded context

    Returns:
        The modules that imported, and a verdict per file that did not
    """
    modules: list[ModuleType] = []
    failures: list[Verdict] = []

    for path in _usecase_files(context_path):
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

    A DTO is a BaseModel. A pydantic dataclass validates too, and is
    still refused: it is a dataclass by every structural test and
    pydantic by its import, so it satisfies the rule for the domain
    ring and the rule for the driving ring at once. One construct that
    passes both is the one thing that cannot say which ring a class is
    in, which is what reading a class is supposed to tell you.

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


def dto_verdicts(slug: str, context_path: Path, names: list[str]) -> list[Verdict]:
    """Resolve DTO names against the context's use case modules.

    A name is looked for as an attribute of any module under
    ``usecases/``, so it is found whether it is defined there or
    imported into it from elsewhere.

    A name that resolves to nothing is a verdict, not a pass. Doctrine
    saw it somewhere and could not reach it, and treating that as
    compliance is how the checked set quietly shrinks.

    Args:
        slug: The bounded context slug
        context_path: Path to the bounded context
        names: The Request or Response class names the parser found

    Returns:
        One verdict per name, plus one per file that would not import
    """
    modules, verdicts = _import_usecase_modules(slug, context_path)

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
            verdicts.append(Verdict(slug, name, _not_a_dto(found)))

    return verdicts
