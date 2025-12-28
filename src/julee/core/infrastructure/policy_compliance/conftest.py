"""Shared fixtures for policy compliance tests.

Policy tests use the same fixtures as doctrine tests - they need
to introspect the target codebase.
"""

import os
from pathlib import Path

import pytest

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
    """Find project root, respecting JULEE_TARGET environment variable."""
    # Check for explicit target override
    target = os.environ.get("JULEE_TARGET")
    if target:
        return Path(target)

    # Default: walk up from this file looking for pyproject.toml
    project_root = Path(__file__).parent
    while project_root.parent != project_root:
        if (project_root / "pyproject.toml").exists():
            return project_root
        project_root = project_root.parent

    # Fallback to current directory
    return Path.cwd()


PROJECT_ROOT = _find_project_root()


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Project root path."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def repo() -> FilesystemBoundedContextRepository:
    """Repository pointing at target codebase."""
    return FilesystemBoundedContextRepository(PROJECT_ROOT)


@pytest.fixture(scope="session")
def app_repo() -> FilesystemApplicationRepository:
    """Application repository pointing at target codebase."""
    return FilesystemApplicationRepository(PROJECT_ROOT)


@pytest.fixture(scope="session")
def solution_repo() -> FilesystemSolutionRepository:
    """Solution repository pointing at target codebase."""
    return FilesystemSolutionRepository(PROJECT_ROOT)


@pytest.fixture(scope="session")
def deployment_repo() -> FilesystemDeploymentRepository:
    """Deployment repository pointing at target codebase."""
    return FilesystemDeploymentRepository(PROJECT_ROOT)


@pytest.fixture(scope="session")
def documentation_repo() -> FilesystemDocumentationRepository:
    """Documentation repository pointing at target codebase."""
    return FilesystemDocumentationRepository(PROJECT_ROOT)
