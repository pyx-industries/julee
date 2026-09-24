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

    Only a solution's own apps may reach a kit's infrastructure or its
    apps: wiring a repository implementation into a composition root is
    the job of a composition root. A bounded context doing the same is
    depending on how a kit stores things rather than on what it offers.

    The caller decides which imports to pass: a solution's apps are left
    out before asking.

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
