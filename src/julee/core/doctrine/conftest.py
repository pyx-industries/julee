"""Shared fixtures for doctrine tests.

Doctrine tests introspect a target codebase. By default, this is the julee
framework itself. To verify an external solution, set JULEE_TARGET:

    JULEE_TARGET=/path/to/solution pytest src/julee/core/doctrine/
"""

import os
from pathlib import Path

import pytest

from julee.core.entities import kernel_entity_names
from julee.core.infrastructure.repositories.file.solution_config import (
    FileSolutionConfigRepository,
)
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)
from julee.core.kits import adopted_kits, viewpoint_slugs
from julee.core.parsers.ast import parse_bounded_context
from julee.core.values.policy import SolutionPolicyConfig


def _find_project_root() -> Path:
    target = os.environ.get("JULEE_TARGET")
    if target:
        target_path = Path(target)
        if not target_path.exists():
            raise ValueError(f"JULEE_TARGET does not exist: {target}")
        return target_path

    project_root = Path(__file__).parent
    while project_root.parent != project_root:
        if (project_root / "pyproject.toml").exists():
            return project_root
        project_root = project_root.parent

    return Path.cwd()


def _get_solution_config(project_root: Path) -> SolutionPolicyConfig:
    return FileSolutionConfigRepository().get_policy_config_sync(project_root)


def _get_search_root(config: SolutionPolicyConfig, project_root: Path) -> str:
    if config.search_root is None:
        raise ValueError(
            f"search_root not configured in [tool.julee] section of "
            f'{project_root}/pyproject.toml. Add: search_root = "src/your_package"'
        )
    return config.search_root


PROJECT_ROOT = _find_project_root()
SOLUTION_CONFIG = _get_solution_config(PROJECT_ROOT)
SEARCH_ROOT = _get_search_root(SOLUTION_CONFIG, PROJECT_ROOT)


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Root of the codebase under test."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def search_root() -> str:
    """Where the target keeps its source, relative to its root."""
    return SEARCH_ROOT


@pytest.fixture(scope="session")
def solution_config() -> SolutionPolicyConfig:
    """The target's own [tool.julee] section, as written."""
    return SOLUTION_CONFIG


@pytest.fixture(scope="session")
def repo() -> FilesystemBoundedContextRepository:
    """Bounded context repository pointing at the target codebase.

    Which contexts count as viewpoints comes from the kits the target
    adopts, so this fixture resolves them first.
    """
    return FilesystemBoundedContextRepository(
        PROJECT_ROOT, SEARCH_ROOT, viewpoint_slugs(PROJECT_ROOT)
    )


@pytest.fixture(scope="session")
def kits():
    """The kits the target codebase adopts."""
    return adopted_kits(PROJECT_ROOT)


def _is_an_enum(entity: object) -> bool:
    """Whether a scanned class is an enum.

    An enum is a value, and one still filed under ``domain/models/`` is
    a value in the wrong directory rather than an aggregate. Read from
    the base name because this is source, not an import.

    Args:
        entity: A class read out of the codebase

    Returns:
        True if any base names an enum
    """
    bases = getattr(entity, "bases", None) or ()
    return any(base.endswith("Enum") for base in bases)


@pytest.fixture(scope="session")
def entity_names_by_context(
    repo: FilesystemBoundedContextRepository,
) -> dict[str, set[str]]:
    """What each context's protocols may be bound to, by context slug.

    A context's own entities, plus the kernel's. A kit builds on
    ``BoundedContextInfo``, ``ClassInfo`` and ``Accelerator`` — there are
    kit repositories over all three — and a protocol bound to one of
    those is bound to an entity like any other. Leaving them out made
    such a repository score zero, which no rule could tell apart from a
    protocol holding nothing at all (#237).

    What is in ``domain/values/`` is left out, because a value object
    has no identity and so nothing is bound to one (ADR 018). That is
    read off the directory rather than guessed from a base class: four
    different guesses preceded this, and each was a different
    approximation of the same idea.

    An enum under ``domain/models/`` is left out too. It is a value that
    has not been moved yet, and reporting it would be noise about
    filing rather than about binding.

    One fixture rather than one construction per rule, because the two
    that read arity disagreed about enums and would have disagreed about
    this too.
    """
    kernel = set(kernel_entity_names())
    found = {}
    for ctx in repo.discover_all():
        info = parse_bounded_context(Path(ctx.path))
        if info is None:
            continue
        found[ctx.slug] = kernel | {e.name for e in info.entities if not _is_an_enum(e)}
    return found
