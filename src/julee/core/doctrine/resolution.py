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


def _is_pydantic(obj: object) -> bool:
    """Whether an object validates its fields the way a DTO must.

    A pydantic dataclass counts. It is not a BaseModel, but it
    validates on construction, which is the whole of what a DTO is
    being asked for here.
    """
    if not isinstance(obj, type):
        return False
    return issubclass(obj, BaseModel) or is_pydantic_dataclass(obj)


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
        elif not _is_pydantic(found):
            verdicts.append(
                Verdict(slug, name, f"{found!r} is not a pydantic model or dataclass")
            )
        else:
            verdicts.append(Verdict(slug, name, None))

    return verdicts
