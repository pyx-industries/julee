"""Where under a bounded context each layer is read from.

A layer has one directory by default: ``usecases/``, ``dtos/``,
``domain/models/``. Under ``domain/`` a context may also divide its
classes by area, the part of the business they belong to, and then a
layer has a directory in each area as well (ADR 023).

Everything that reads a layer asks here, so that the class parser, the
resolver that imports what the parser found, and discovery agree on
where a layer is.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from julee.core.doctrine_constants import (
    DOMAIN_KIND_DIRECTORIES,
    DOMAIN_PATH,
    ENTITIES_PATH,
)
from julee.core.parsers.ast import is_test_file

__all__ = [
    "LayerDirectory",
    "areas_of",
    "kind_directory_of",
    "layer_directories",
    "python_files_in",
]


@dataclass(frozen=True)
class LayerDirectory:
    """One directory a layer is read from."""

    path: Path
    files_relative_to: Path
    """What the path of a file read here is counted from.

    The directory itself for a layer's own directory, as it has always
    been. ``domain/`` for a directory in an area, so that a class says
    which area it was read in.
    """
    with_subdirectories: bool = True
    """Whether what lies beneath the directory belongs to the layer too.

    False for an area read as entities: the directories inside an area
    are read by their own names.
    """


def _is_read(directory: Path) -> bool:
    """Whether a directory under domain/ is one a layer could be read from."""
    name = directory.name
    return directory.is_dir() and not name.startswith((".", "__")) and name != "tests"


def _areas_and_kinds(directory: Path) -> tuple[list[Path], list[Path]]:
    """The areas beneath a directory, and the kind directories inside them."""
    areas: list[Path] = []
    kinds: list[Path] = []
    for child in sorted(directory.iterdir()):
        if not _is_read(child):
            continue
        if child.name in DOMAIN_KIND_DIRECTORIES:
            kinds.append(child)
            continue
        areas.append(child)
        nested_areas, nested_kinds = _areas_and_kinds(child)
        areas.extend(nested_areas)
        kinds.extend(nested_kinds)
    return areas, kinds


def areas_of(context_dir: Path) -> list[Path]:
    """The areas a bounded context divides its domain into.

    A directory under ``domain/`` whose name is not a kind's is an area,
    and so is such a directory inside an area. What lies beneath a kind
    directory belongs to that kind and is not looked at here.

    Args:
        context_dir: The bounded context

    Returns:
        Each area's directory, sorted by path
    """
    domain = context_dir.joinpath(*DOMAIN_PATH)
    if not domain.is_dir():
        return []
    areas, _ = _areas_and_kinds(domain)
    return areas


def layer_directories(
    context_dir: Path, layer: tuple[str, ...]
) -> list[LayerDirectory]:
    """Every directory a bounded context's layer is read from.

    The layer's own directory comes first, whether or not it exists. For
    a layer under ``domain/`` the directory of the same name in each
    area follows it, and for entities each area itself: a module an area
    holds directly is read as entities.

    Args:
        context_dir: The bounded context
        layer: Path segments of the layer, e.g. ("domain", "repositories")

    Returns:
        The directories, the layer's own first
    """
    own = context_dir.joinpath(*layer)
    found = [LayerDirectory(path=own, files_relative_to=own)]

    domain = context_dir.joinpath(*DOMAIN_PATH)
    if layer[: len(DOMAIN_PATH)] != DOMAIN_PATH or not domain.is_dir():
        return found

    areas, kinds = _areas_and_kinds(domain)
    if layer == ENTITIES_PATH:
        found.extend(
            LayerDirectory(
                path=area, files_relative_to=domain, with_subdirectories=False
            )
            for area in areas
        )
    found.extend(
        LayerDirectory(path=kind, files_relative_to=domain)
        for kind in kinds
        if kind.name == layer[-1] and kind != own
    )
    return found


def python_files_in(directory: LayerDirectory) -> list[Path]:
    """The modules one of a layer's directories holds, tests left out.

    Args:
        directory: A directory a layer is read from

    Returns:
        Its ``.py`` files, with those beneath it if they belong to the layer
    """
    if not directory.path.is_dir():
        return []
    pattern = "**/*.py" if directory.with_subdirectories else "*.py"
    return sorted(
        path for path in directory.path.glob(pattern) if not is_test_file(path)
    )


def kind_directory_of(file: Sequence[str]) -> str | None:
    """The kind directory a file under ``domain/`` is read as part of.

    The first directory on the way down from ``domain/`` whose name is a
    kind's. Whatever is beneath that directory belongs to it, so a
    kind's name further down decides nothing.

    Args:
        file: Path segments of the file from the bounded context, e.g.
            ("domain", "billing", "repositories", "invoice.py")

    Returns:
        The kind directory's name, or None if the file is not under
        ``domain/`` or is in no kind directory
    """
    if tuple(file[: len(DOMAIN_PATH)]) != DOMAIN_PATH:
        return None
    return next(
        (
            segment
            for segment in file[len(DOMAIN_PATH) : -1]
            if segment in DOMAIN_KIND_DIRECTORIES
        ),
        None,
    )
