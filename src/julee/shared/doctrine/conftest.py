"""Shared fixtures for doctrine tests."""

from pathlib import Path

import pytest

from julee.shared.repositories.introspection import FilesystemBoundedContextRepository

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


@pytest.fixture
def project_root() -> Path:
    """Project root path."""
    return PROJECT_ROOT


def create_bounded_context(
    base_path: Path, name: str, layers: list[str] | None = None
) -> Path:
    """Helper to create a bounded context directory structure."""
    ctx_path = base_path / name
    ctx_path.mkdir(parents=True)
    (ctx_path / "__init__.py").touch()
    for layer in layers or ["models", "use_cases"]:
        layer_path = ctx_path / "domain" / layer
        layer_path.mkdir(parents=True)
    return ctx_path


def create_solution(tmp_path: Path) -> Path:
    """Create a solution root with standard structure."""
    root = tmp_path / "src" / "julee"
    root.mkdir(parents=True)
    return root
