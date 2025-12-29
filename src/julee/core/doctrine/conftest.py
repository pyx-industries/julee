"""Shared fixtures for doctrine tests.

Doctrine tests introspect a target codebase. By default, this is the julee
framework itself. To verify an external solution, set JULEE_TARGET:

    JULEE_TARGET=/path/to/solution pytest src/julee/core/doctrine/

Or use julee-admin:

    julee-admin doctrine verify --target /path/to/solution
"""

import os
from pathlib import Path

import pytest

from julee.core.doctrine_constants import (
    ENTITIES_PATH,
    USE_CASES_PATH,
)
from julee.core.infrastructure.repositories.file.solution_config import (
    FileSolutionConfigRepository,
)
from julee.core.infrastructure.repositories.introspection.application import (
    FilesystemApplicationRepository,
)
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)
from julee.core.infrastructure.repositories.introspection.deployment import (
    FilesystemDeploymentRepository,
)
from julee.core.infrastructure.repositories.introspection.documentation import (
    FilesystemDocumentationRepository,
)
from julee.core.infrastructure.repositories.introspection.solution import (
    FilesystemSolutionRepository,
)


def _find_project_root() -> Path:
    """Find project root, respecting JULEE_TARGET environment variable.

    Priority:
    1. JULEE_TARGET env var (explicit target)
    2. Walk up from this file to find pyproject.toml (default: julee itself)
    """
    # Check for explicit target override
    target = os.environ.get("JULEE_TARGET")
    if target:
        target_path = Path(target)
        if not target_path.exists():
            raise ValueError(f"JULEE_TARGET does not exist: {target}")
        return target_path

    # Default: walk up from this file looking for pyproject.toml
    project_root = Path(__file__).parent
    while project_root.parent != project_root:
        if (project_root / "pyproject.toml").exists():
            return project_root
        project_root = project_root.parent

    # Fallback to current directory
    return Path.cwd()


PROJECT_ROOT = _find_project_root()


def _get_search_root(project_root: Path) -> str:
    """Get search_root from pyproject.toml [tool.julee] config.

    Raises:
        ValueError: If search_root is not configured
    """
    repo = FileSolutionConfigRepository()
    config = repo.get_policy_config_sync(project_root)
    if config.search_root is None:
        raise ValueError(
            f"search_root not configured in [tool.julee] section of "
            f"{project_root}/pyproject.toml. Add: search_root = \"src/your_package\""
        )
    return config.search_root


SEARCH_ROOT = _get_search_root(PROJECT_ROOT)


@pytest.fixture(scope="session")
def repo() -> FilesystemBoundedContextRepository:
    """Repository pointing at real codebase.

    Session-scoped to avoid re-discovering bounded contexts for each test.
    The repository caches its discovery results internally.
    """
    return FilesystemBoundedContextRepository(PROJECT_ROOT, SEARCH_ROOT)


@pytest.fixture(scope="session")
def app_repo() -> FilesystemApplicationRepository:
    """Application repository pointing at real codebase.

    Session-scoped to avoid re-discovering applications for each test.
    The repository caches its discovery results internally.
    """
    return FilesystemApplicationRepository(PROJECT_ROOT)


@pytest.fixture(scope="session")
def solution_repo() -> FilesystemSolutionRepository:
    """Solution repository pointing at real codebase.

    Session-scoped to avoid re-discovering the solution structure for each test.
    The repository caches its discovery results internally.
    """
    return FilesystemSolutionRepository(PROJECT_ROOT, SEARCH_ROOT)


@pytest.fixture(scope="session")
def deployment_repo() -> FilesystemDeploymentRepository:
    """Deployment repository pointing at real codebase.

    Session-scoped to avoid re-discovering deployments for each test.
    The repository caches its discovery results internally.
    """
    return FilesystemDeploymentRepository(PROJECT_ROOT)


@pytest.fixture(scope="session")
def documentation_repo() -> FilesystemDocumentationRepository:
    """Documentation repository pointing at real codebase.

    Session-scoped to avoid re-discovering documentation for each test.
    The repository caches its discovery results internally.
    """
    return FilesystemDocumentationRepository(PROJECT_ROOT)


@pytest.fixture
def project_root() -> Path:
    """Project root path."""
    return PROJECT_ROOT


@pytest.fixture
def search_root() -> str:
    """Search root path (relative to project_root)."""
    return SEARCH_ROOT


def create_bounded_context(
    base_path: Path, name: str, layers: list[str] | None = None
) -> Path:
    """Helper to create a bounded context directory structure.

    Creates the flattened structure: {bc}/entities/, {bc}/use_cases/
    """
    ctx_path = base_path / name
    ctx_path.mkdir(parents=True)
    (ctx_path / "__init__.py").touch()

    # Default layers: entities and use_cases (flattened, no domain/ nesting)
    default_layers = [
        ENTITIES_PATH,  # ("entities",)
        USE_CASES_PATH,  # ("use_cases",)
    ]
    for layer_path_tuple in layers or default_layers:
        # Handle both old-style string and new-style tuple paths
        if isinstance(layer_path_tuple, str):
            layer_path = ctx_path / layer_path_tuple
        else:
            layer_path = ctx_path
            for part in layer_path_tuple:
                layer_path = layer_path / part
        layer_path.mkdir(parents=True)
    return ctx_path


def create_solution(tmp_path: Path) -> Path:
    """Create a solution root with standard structure."""
    root = tmp_path / "src" / "julee"
    root.mkdir(parents=True)
    return root
