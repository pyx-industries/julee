"""What the dependency rule objects to.

Clean architecture's one rule is that source dependencies point
inward. A use case may reach for the ring inside it, its own ring, and
the language. Everything further out — frameworks, adapters, drivers,
serialisation, the filesystem — is a detail it must not know.

Each rule takes the imports a codebase makes and returns its
objections. Nothing here reads a file or imports a module: an import
statement names the module it imports, so unlike a type annotation it
cannot be read wrong.
"""

import sys
from collections.abc import Iterable

from julee.core.parsers.imports import ImportInfo

__all__ = [
    "INWARD_JULEE_PACKAGES",
    "LANGUAGE_MODULES",
    "OUTWARD_JULEE_PACKAGES",
    "USE_CASE_PACKAGES",
    "absolute_module",
    "usecases_importing_outward",
]

LANGUAGE_MODULES = frozenset(
    {
        "__future__",
        "abc",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "enum",
        "typing",
        "uuid",
    }
)
"""The standard library a use case may speak.

An allow-list, so a module arrives here by decision. Most of the
standard library is the outside world with a standard-library badge:
``json`` picks a representation, ``pathlib`` hands over a file to
read, ``random`` and ``time`` are non-determinism that ADR 016 puts
behind a Witness.

``collections.abc`` is here and ``collections`` is not: one is
vocabulary for talking about sequences, the other is mutable
containers.
"""

USE_CASE_PACKAGES = ("domain", "usecases")
"""The parts of its own bounded context a use case may reach for.

Its ring and the ring inside it. ``infrastructure`` and ``apps`` are
the two it may not, and they are the two a kit does not offer either
(ADR 012 §3).
"""

OUTWARD_JULEE_PACKAGES = (
    "julee.cli",
    "julee.core.infrastructure",
    "julee.integrations",
    "julee.maintenance",
    "julee.repositories",
)
"""julee's own adapters and drivers.

``julee.repositories`` holds the file and memory mixins, which are
implementations; the protocols they implement live in
``julee.core.repositories`` and are inward.
"""

INWARD_JULEE_PACKAGES = ("julee",)
"""Everything else julee offers — entities, ports, use case bases."""


def absolute_module(info: ImportInfo, package: str) -> str:
    """The module an import names, relative ones resolved.

    Args:
        info: One import
        package: The package of the file the import is in

    Returns:
        A dotted module path
    """
    if not info.is_relative:
        return info.module

    parts = package.split(".")
    climbed = parts[: len(parts) - (info.level - 1)] if info.level > 1 else parts
    return ".".join([*climbed, info.module]) if info.module else ".".join(climbed)


def _is_within(module: str, package: str) -> bool:
    """Whether a module path names something in a package."""
    return module == package or module.startswith(f"{package}.")


def _why_forbidden(module: str, context_package: str, kit_packages: frozenset[str]):
    """Why a use case may not import a module, or None if it may.

    Args:
        module: The absolute module path
        context_package: The package of the bounded context importing it
        kit_packages: Packages of the kits the solution adopts

    Returns:
        A clause for the objection, or None
    """
    if _is_within(module, context_package):
        rest = module[len(context_package) :].lstrip(".")
        if rest.split(".")[0] in USE_CASE_PACKAGES:
            return None
        where = rest.split(".")[0] or context_package
        return f"{where} is outside the domain and the use cases"

    for package in kit_packages:
        if _is_within(module, package):
            rest = module[len(package) :].lstrip(".")
            if rest.split(".")[0] in USE_CASE_PACKAGES:
                return None
            return f"it is {package}'s {rest.split('.')[0]}, not what the kit offers"

    if any(_is_within(module, package) for package in INWARD_JULEE_PACKAGES):
        for package in OUTWARD_JULEE_PACKAGES:
            if _is_within(module, package):
                return "it is one of julee's adapters"
        return None

    top = module.split(".")[0]
    if module in LANGUAGE_MODULES or any(
        module.startswith(f"{allowed}.") for allowed in LANGUAGE_MODULES
    ):
        return None
    if top in sys.stdlib_module_names:
        return "it is in the standard library but not part of the language a use case speaks"
    return "it is a third-party package"


def usecases_importing_outward(
    imports: Iterable[tuple[str, str, ImportInfo]],
    context_packages: dict[str, str],
    kit_packages: Iterable[str] = (),
) -> list[str]:
    """Use cases reaching for something further out than themselves.

    A use case may import its own context's ``domain/`` and
    ``usecases/``, an adopted kit's same two, julee's entities, ports
    and use case bases, and the handful of standard library modules in
    :data:`LANGUAGE_MODULES`. Anything else is a detail.

    Imports anywhere in a file count, including one deferred inside a
    function, which is a common way to reach somewhere a file may not.

    Args:
        imports: Bounded context slug, the importing file's package,
            and one import
        context_packages: Package path, by bounded context slug
        kit_packages: Packages of the kits the solution adopts

    Returns:
        One sentence per import that points outward
    """
    kits = frozenset(kit_packages)

    objections = []
    for slug, package, info in imports:
        module = absolute_module(info, package)
        reason = _why_forbidden(module, context_packages.get(slug, slug), kits)
        if reason is not None:
            objections.append(f"{info.file}:{info.line} imports {module}, but {reason}")
    return objections
