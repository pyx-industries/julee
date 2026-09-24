"""What the boundary rules object to.

ADR 012 §3 says two things about reaching across the kit boundary, and
until now said them only in prose. Both are about a solution's own code:
what it may import, and how far into a kit it may reach.

Each takes the imports a codebase makes and returns its objections.
Nothing here reads a file or imports a module.
"""

from collections.abc import Iterable

from julee.core.parsers.imports import ImportInfo

__all__ = [
    "KIT_INTERNALS",
    "imports_of_unadopted_kits",
    "imports_reaching_into_a_kit",
    "within_a_composition_root",
]

KIT_INTERNALS = ("infrastructure", "apps")
"""The parts of a kit only a solution's own apps may reach for.

A kit's entities, use cases and protocols are what it offers. How it
stores things and how it is served are its own business, and a bounded
context reaching for either is coupling itself to decisions the kit is
entitled to change.
"""


def _is_within(module: str, package: str) -> bool:
    """Whether a module path names something in a package."""
    return module == package or module.startswith(f"{package}.")


def within_a_composition_root(
    parts: tuple[str, ...], composition_roots: Iterable[str]
) -> bool:
    """Whether a file sits under one of the declared composition roots.

    A composition root chooses implementations and wires them together,
    so it is the one place entitled to reach for a kit's infrastructure.
    Which directories those are is declared, because the role is not
    always held by a directory called apps/: julee-viewpoints wires its
    repositories in ``sphinx_c4/sphinx/context.py``, attached to the
    Sphinx application at builder-inited, which is a composition root by
    every test except its name.

    A root matches as a contiguous run of directory names anywhere in the
    path, not only at the front. That is what "apps" already meant — a
    bounded context's own apps/ counted wherever it sat — and a
    multi-segment root like "sphinx_c4/sphinx" is read the same way.

    Args:
        parts: The file's path segments, relative to the search root
        composition_roots: Declared roots, e.g. ("apps",) or
            ("sphinx_c4/sphinx",)

    Returns:
        True if the file is inside one of them
    """
    for root in composition_roots:
        needle = tuple(segment for segment in root.split("/") if segment)
        if not needle:
            continue
        span = len(needle)
        if any(
            parts[start : start + span] == needle
            for start in range(len(parts) - span + 1)
        ):
            return True
    return False


def imports_of_unadopted_kits(
    imports: Iterable[ImportInfo],
    unadopted_packages: dict[str, str],
) -> list[str]:
    """Imports of a kit the solution has not adopted.

    Adoption is what makes a kit part of a solution. A kit that happens
    to be installed — pulled in by something else — is not, and importing
    it anyway means the solution depends on something it never declared
    and nothing will keep installing for it.

    Args:
        imports: The imports a codebase makes
        unadopted_packages: Package name to kit slug, for installed kits
            the solution does not adopt

    Returns:
        One sentence per import that should not be there
    """
    return [
        f"{info.file}:{info.line} imports {info.module}, which belongs to "
        f"{slug}, a kit this solution has not adopted"
        for info in imports
        for package, slug in unadopted_packages.items()
        if _is_within(info.module, package)
    ]


def imports_reaching_into_a_kit(
    imports: Iterable[ImportInfo],
    kit_packages: Iterable[str],
) -> list[str]:
    """Imports of a kit's insides from somewhere that may not.

    Only a solution's composition roots may reach a kit's infrastructure
    or its apps: wiring a repository implementation in is the job of a
    composition root. A bounded context doing the same is depending on
    how a kit stores things rather than on what it offers.

    The caller decides which imports to pass: files under a composition
    root are left out first, using :func:`within_a_composition_root`.

    Args:
        imports: The imports to check, a solution's apps excluded
        kit_packages: The packages of the kits the solution adopts

    Returns:
        One sentence per import reaching too far
    """
    return [
        f"{info.file}:{info.line} imports {info.module}, which is "
        f"{package}'s {part} and not part of what the kit offers"
        for info in imports
        for package in kit_packages
        for part in KIT_INTERNALS
        if _is_within(info.module, f"{package}.{part}")
    ]
