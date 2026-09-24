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

import importlib
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
    "contributed_objects",
    "contributions",
    "resolve_contribution",
    "sphinx_extensions",
    "installed_kits",
    "kit_context_slugs",
    "own_kit",
    "own_packages",
    "unresolved_kit_slugs",
    "viewpoint_slugs",
]


def installed_kits() -> tuple[Kit, ...]:
    """Every installed kit, whether or not a solution adopts it."""
    return tuple(EntryPointKitRepository().list_all_sync())


def own_packages(solution_root: Path) -> frozenset[str]:
    """The top-level packages a codebase ships itself.

    Read from the layout rather than from ``search_root``, which points
    at different depths in different kits.

    Args:
        solution_root: Path to the solution root directory

    Returns:
        Package names, e.g. ``{"julee_hcd"}``
    """
    source = solution_root / "src"
    if not source.is_dir():
        source = solution_root
    if not source.is_dir():
        return frozenset()
    return frozenset(
        directory.name
        for directory in source.iterdir()
        if directory.is_dir() and (directory / "__init__.py").exists()
    )


def own_kit(solution_root: Path) -> Kit | None:
    """The kit this codebase is, if it is one.

    A kit is a julee solution in its own right and does not adopt
    itself, so its own manifest is not in :func:`adopted_kits`. It is
    installed, though — an editable install in its own workspace — so it
    can be recognised by the package it ships.

    Args:
        solution_root: Path to the solution root directory

    Returns:
        The manifest, or None when the codebase is not a kit
    """
    packages = own_packages(solution_root)
    for kit in installed_kits():
        if kit.package in packages:
            return kit
    return None


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


def contributions(solution_root: Path, point: str) -> tuple[str, ...]:
    """What the adopted kits offer at one contribution point.

    Dotted paths, not objects: reading a manifest imports nothing, and
    that holds here too. Whichever integration knows the technology
    resolves them — a Sphinx extension list is strings already, so it
    needs no resolving at all.

    Kits are asked in the order the solution adopts them, so a solution
    controls the order its contributions arrive in by the order it lists
    its kits.

    Args:
        solution_root: Path to the solution root directory
        point: The contribution point, e.g. "temporal.activities"

    Returns:
        Every path offered at that point, in adoption order
    """
    return tuple(
        path for kit in adopted_kits(solution_root) for path in kit.contributed(point)
    )


def sphinx_extensions(solution_root: Path) -> list[str]:
    """The Sphinx extensions the adopted kits provide.

    For a solution's conf.py::

        from julee.core.kits import sphinx_extensions

        extensions = [*sphinx_extensions(Path(__file__).parent.parent)]

    A list because that is what Sphinx expects to be given, and because a
    solution will usually add extensions of its own to it.

    Args:
        solution_root: Path to the solution root directory

    Returns:
        Extension module paths, in adoption order
    """
    return list(contributions(solution_root, "sphinx.extension"))


def resolve_contribution(path: str) -> object:
    """Import what a contribution names.

    A path names exactly one thing. ``a.b.c`` is the module; ``a.b:c`` is
    the attribute ``c`` inside module ``a.b``. A bare module never means
    "look inside this for anything that qualifies": a contribution point
    that wants several things is pointed at something that holds them,
    so what is offered is written in the kit and not inferred by
    whatever reads it.

    Importing happens here and nowhere earlier. Reading a manifest and
    asking what is contributed both stay free of it; only a caller that
    actually wants the object pays.

    Args:
        path: A contribution path, with or without an attribute

    Returns:
        The module, or the attribute inside it

    Raises:
        ImportError: If the module is not there
        AttributeError: If the module has no such attribute
    """
    module_path, _, attribute = path.partition(":")
    module = importlib.import_module(module_path)
    if not attribute:
        return module
    return getattr(module, attribute)


def contributed_objects(kit: Kit, point: str) -> tuple[object, ...]:
    """Everything one kit offers at a point, imported.

    A contribution path names one thing, but that thing is often a tuple
    holding several — a kit with eight activity classes points at one
    tuple rather than writing eight paths. This resolves each path and
    flattens a tuple or list it finds, so a caller gets the objects
    whichever way the kit chose to write them.

    Only one level is flattened, and only a tuple or list. Whatever the
    members turn out to be — classes, module names — they are passed on
    as they were found.

    Args:
        kit: The kit to ask
        point: The contribution point, e.g. "temporal.activities"

    Returns:
        The contributed objects, in the order the kit declares them

    Raises:
        ImportError: If a path names a module that is not there
        AttributeError: If a path names an attribute that is not there
    """
    found: list[object] = []
    for path in kit.contributed(point):
        resolved = resolve_contribution(path)
        if isinstance(resolved, list | tuple):
            found.extend(resolved)
        else:
            found.append(resolved)
    return tuple(found)
