"""Shared fixtures for doctrine tests."""

from pathlib import Path

import pytest

from julee.core.doctrine_constants import (
    ENTITIES_PATH,
    USE_CASES_PATH,
)
from julee.core.infrastructure.repositories.introspection import (
    FilesystemApplicationRepository,
    FilesystemBoundedContextRepository,
    FilesystemSolutionRepository,
)

# Project root - find by looking for pyproject.toml
PROJECT_ROOT = Path(__file__).parent
while PROJECT_ROOT.parent != PROJECT_ROOT:
    if (PROJECT_ROOT / "pyproject.toml").exists():
        break
    PROJECT_ROOT = PROJECT_ROOT.parent


@pytest.fixture(scope="session")
def repo() -> FilesystemBoundedContextRepository:
    """Repository pointing at real codebase.

    Session-scoped to avoid re-discovering bounded contexts for each test.
    The repository caches its discovery results internally.
    """
    return FilesystemBoundedContextRepository(PROJECT_ROOT)


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
    return FilesystemSolutionRepository(PROJECT_ROOT)


@pytest.fixture
def project_root() -> Path:
    """Project root path."""
    return PROJECT_ROOT


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
