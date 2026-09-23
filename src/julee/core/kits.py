"""Resolving which kits a solution has adopted.

Two questions are distinct, and both matter:

- Which kits are *installed*? Whatever registered a ``julee.kits`` entry
  point, including transitive dependencies.
- Which kits has the solution *adopted*? Only the slugs in
  ``[tool.julee] kits``.

Doctrine, composition and documentation all work from the adopted set. The
installed set is only used to resolve those slugs and to report a slug that
names nothing.
"""

import importlib.util
from pathlib import Path

from julee.core.entities.kit import Kit
from julee.core.infrastructure.repositories.entry_points.kit import (
    EntryPointKitRepository,
)
from julee.core.infrastructure.repositories.file.solution_config import (
    FileSolutionConfigRepository,
)
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)

__all__ = [
    "adopted_kits",
    "installed_kits",
    "kit_context_slugs",
    "unresolved_kit_slugs",
    "viewpoint_slugs",
]


def installed_kits() -> tuple[Kit, ...]:
    """Every installed kit, whether or not a solution adopts it."""
    return tuple(EntryPointKitRepository().list_all_sync())


def adopted_kits(solution_root: Path) -> tuple[Kit, ...]:
    """The kits a solution adopts, in the order it declares them.

    A declared slug that is not installed is left out; see
    :func:`unresolved_kit_slugs`.

    Args:
        solution_root: Path to the solution root directory
    """
    declared = FileSolutionConfigRepository().get_policy_config_sync(solution_root).kits
    by_slug = {kit.slug: kit for kit in installed_kits()}
    return tuple(by_slug[slug] for slug in declared if slug in by_slug)


def unresolved_kit_slugs(solution_root: Path) -> tuple[str, ...]:
    """Slugs the solution adopts that no installed kit provides.

    Args:
        solution_root: Path to the solution root directory
    """
    declared = FileSolutionConfigRepository().get_policy_config_sync(solution_root).kits
    installed = {kit.slug for kit in installed_kits()}
    return tuple(slug for slug in declared if slug not in installed)


def kit_context_slugs(kit: Kit) -> frozenset[str]:
    """Slugs of the bounded contexts a kit provides.

    Found by introspecting the kit's installed package, so a kit does not
    restate in its manifest what its own layout already says. An
    uninstallable or unlocatable package yields nothing.

    Args:
        kit: The kit to introspect
    """
    try:
        spec = importlib.util.find_spec(kit.package)
    except (ImportError, ValueError):
        return frozenset()
    if spec is None or not spec.submodule_search_locations:
        return frozenset()
    package_dir = Path(next(iter(spec.submodule_search_locations)))
    repo = FilesystemBoundedContextRepository(package_dir.parent, package_dir.name)

    # A kit is laid out one of two ways, and both are legitimate: the
    # package holds its contexts (julee-viewpoints holds sphinx_hcd), or
    # the package is the context (julee-ceap, julee-polling).
    inside = frozenset(context.slug for context in repo.discover_all())
    if inside:
        return inside

    itself = repo.describe(package_dir)
    return frozenset({itself.slug}) if itself else frozenset()


def viewpoint_slugs(solution_root: Path) -> frozenset[str]:
    """Bounded-context slugs that are viewpoints rather than domains.

    A viewpoint describes a solution instead of implementing part of it.
    Which contexts those are is declared by the kits that provide them
    (``viewpoint = True``), not known to the framework in advance.

    Args:
        solution_root: Path to the solution root directory
    """
    slugs: set[str] = set()
    for kit in adopted_kits(solution_root):
        if kit.viewpoint:
            slugs |= kit_context_slugs(kit)
    return frozenset(slugs)
