"""Shared fixtures for doctrine tests.

Doctrine tests introspect a target codebase. By default, this is the julee
framework itself. To verify an external solution, set JULEE_TARGET:

    JULEE_TARGET=/path/to/solution pytest src/julee/core/doctrine/
"""

import os
from pathlib import Path

import pytest

from julee.core.infrastructure.repositories.file.solution_config import (
    FileSolutionConfigRepository,
)
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)


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


def _get_search_root(project_root: Path) -> str:
    repo = FileSolutionConfigRepository()
    config = repo.get_policy_config_sync(project_root)
    if config.search_root is None:
        raise ValueError(
            f"search_root not configured in [tool.julee] section of "
            f'{project_root}/pyproject.toml. Add: search_root = "src/your_package"'
        )
    return config.search_root


PROJECT_ROOT = _find_project_root()
SEARCH_ROOT = _get_search_root(PROJECT_ROOT)


@pytest.fixture(scope="session")
def repo() -> FilesystemBoundedContextRepository:
    """Bounded context repository pointing at the target codebase."""
    return FilesystemBoundedContextRepository(PROJECT_ROOT, SEARCH_ROOT)
