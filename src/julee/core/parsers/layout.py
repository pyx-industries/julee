"""Where under a bounded context each layer is read from.

A layer outside ``domain/`` has one directory: ``usecases/``, ``dtos/``.
A layer under ``domain/`` is a kind of class, and is read from wherever
that kind's name stands: a directory or a module called ``models``,
``repositories``, ``errors`` and so on, directly under ``domain/`` or
in an area of it (ADR 023, ADR 024). Every other module under
``domain/`` is read as entities.

Everything that reads a layer asks here, so that the class parser, the
resolver that imports what the parser found, and discovery agree on
where a layer is.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from julee.core.doctrine_constants import (
    DOMAIN_KIND_DIRECTORIES,
    DOMAIN_PATH,
    ENTITIES_PATH,
)
from julee.core.parsers.ast import is_test_file

__all__ = [
    "LayerFile",
    "areas_of",
    "kind_of",
    "layer_files",
]


@dataclass(frozen=True)
class LayerFile:
    """One module a layer is read from."""

    path: Path
    counted_from: Path
    """What the path recorded for a class in this module is counted from.

    The layer's own directory for a module inside it, as it has always
    been. ``domain/`` for a module anywhere else, so that a class says
    which area it was read in.
    """


@dataclass
class _Domain:
    """What a walk of ``domain/`` found, each list sorted by path."""

    areas: list[Path] = field(default_factory=list)
    kinds: list[Path] = field(default_factory=list)
    """Directories and modules named for a kind."""
    modules: list[Path] = field(default_factory=list)
    """Modules named for no kind, held by ``domain/`` or by an area."""


def _is_read(directory: Path) -> bool:
    """Whether a directory under domain/ is one a layer could be read from."""
    name = directory.name
    return not name.startswith((".", "__")) and name != "tests"


def _walk(directory: Path, found: _Domain) -> None:
    """Sort what ``domain/`` or an area holds, and what its areas hold.

    What lies beneath a directory named for a kind belongs to the kind,
    and is not looked at here.
    """
    for child in sorted(directory.iterdir()):
        if child.is_dir():
            if not _is_read(child):
                continue
            if child.name in DOMAIN_KIND_DIRECTORIES:
                found.kinds.append(child)
                continue
            found.areas.append(child)
            _walk(child, found)
        elif child.suffix == ".py":
            if child.stem in DOMAIN_KIND_DIRECTORIES:
                found.kinds.append(child)
            else:
                found.modules.append(child)


def _domain_of(context_dir: Path) -> tuple[Path, _Domain]:
    """A bounded context's ``domain/`` and what a walk of it finds."""
    domain = context_dir.joinpath(*DOMAIN_PATH)
    found = _Domain()
    if domain.is_dir():
        _walk(domain, found)
    return domain, found


def _modules_in(directory: Path) -> list[Path]:
    """Every module in a directory and beneath it, tests left out."""
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.rglob("*.py") if not is_test_file(path))


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
    _, found = _domain_of(context_dir)
    return found.areas


def layer_files(context_dir: Path, layer: tuple[str, ...]) -> list[LayerFile]:
    """Every module a bounded context's layer is read from.

    For a layer outside ``domain/``, the modules of its directory and
    beneath. For a layer under ``domain/``, the modules of each
    directory named for the kind, and each module named for it, whether
    directly under ``domain/`` or in an area. Entities have more: a
    module ``domain/`` or an area holds that is named for no kind is
    read as entities.

    Test files are left out, as they are everywhere doctrine reads.

    Args:
        context_dir: The bounded context
        layer: Path segments of the layer, e.g. ("domain", "repositories")

    Returns:
        The modules, those of the layer's own directory first
    """
    own = context_dir.joinpath(*layer)
    if layer[: len(DOMAIN_PATH)] != DOMAIN_PATH:
        return [LayerFile(path, counted_from=own) for path in _modules_in(own)]

    domain, found = _domain_of(context_dir)
    files = [LayerFile(path, counted_from=own) for path in _modules_in(own)]
    for kind in found.kinds:
        if kind == own or kind.name.removesuffix(".py") != layer[-1]:
            continue
        modules = _modules_in(kind) if kind.is_dir() else [kind]
        files.extend(LayerFile(path, counted_from=domain) for path in modules)
    if layer == ENTITIES_PATH:
        files.extend(
            LayerFile(path, counted_from=domain)
            for path in found.modules
            if not is_test_file(path)
        )
    return files


def kind_of(file: Sequence[str]) -> str | None:
    """The kind a file under ``domain/`` is read as, if a name says so.

    The first directory on the way down from ``domain/`` whose name is a
    kind's, or failing that the module's own name. Whatever is beneath a
    kind directory belongs to it, so a kind's name further down decides
    nothing.

    Args:
        file: Path segments of the file from the bounded context, e.g.
            ("domain", "billing", "repositories", "invoice.py")

    Returns:
        The kind's name, or None if the file is not under ``domain/`` or
        no name on its path is a kind's
    """
    if tuple(file[: len(DOMAIN_PATH)]) != DOMAIN_PATH or len(file) <= len(DOMAIN_PATH):
        return None
    *directories, module = file[len(DOMAIN_PATH) :]
    for segment in directories:
        if segment in DOMAIN_KIND_DIRECTORIES:
            return segment
    stem = module.removesuffix(".py")
    return stem if stem in DOMAIN_KIND_DIRECTORIES else None
