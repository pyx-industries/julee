"""Shared fixtures for doctrine tests.

Doctrine tests introspect a target codebase. By default, this is the julee
framework itself. To verify an external solution, set JULEE_TARGET:

    JULEE_TARGET=/path/to/solution pytest src/julee/core/doctrine/
"""

import os
from pathlib import Path

import pytest

from julee.core.entities.policy import SolutionPolicyConfig
from julee.core.infrastructure.repositories.file.solution_config import (
    FileSolutionConfigRepository,
)
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)
from julee.core.kits import adopted_kits, viewpoint_slugs


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
