"""Dependency injection for julee-admin CLI.

Provides a DI container that constructs use cases with appropriate
repository implementations. Follows the same patterns as the API
applications but adapted for CLI context.
"""

import os
from functools import lru_cache
from pathlib import Path

from julee.core.use_cases import (
    GetBoundedContextUseCase,
    ListBoundedContextsUseCase,
    ListEntitiesUseCase,
    ListRepositoryProtocolsUseCase,
    ListRequestsUseCase,
    ListResponsesUseCase,
    ListServiceProtocolsUseCase,
    ListUseCasesUseCase,
)
from julee.core.infrastructure.repositories.introspection import FilesystemBoundedContextRepository


PROJECT_ROOT_MARKERS = ("pyproject.toml", "setup.py", ".git")


def find_project_root(start_path: Path | None = None) -> Path:
    """Find the project root by walking up from start_path.

    Looks for common project markers (pyproject.toml, setup.py, .git)
    to identify the project root.

    Args:
        start_path: Path to start searching from. Defaults to cwd.

    Returns:
        Path to the project root, or cwd if not found.
    """
    path = start_path or Path.cwd()
    path = path.resolve()

    for parent in [path, *path.parents]:
        for marker in PROJECT_ROOT_MARKERS:
            if (parent / marker).exists():
                return parent

    # Fall back to cwd if no markers found
    return Path.cwd()


def get_project_root() -> Path:
    """Get the project root directory.

    Uses JULEE_PROJECT_ROOT environment variable if set,
    otherwise attempts to find the project root by looking
    for common markers (pyproject.toml, setup.py, .git).

    Returns:
        Path to the project root directory
    """
    root = os.getenv("JULEE_PROJECT_ROOT")
    if root:
        return Path(root)
    return find_project_root()


@lru_cache
def get_bounded_context_repository() -> FilesystemBoundedContextRepository:
    """Get the bounded context repository singleton.

    Returns:
        Repository for discovering bounded contexts in the filesystem
    """
    return FilesystemBoundedContextRepository(get_project_root())


# =============================================================================
# Bounded Context Use Cases
# =============================================================================


def get_list_bounded_contexts_use_case() -> ListBoundedContextsUseCase:
    """Get ListBoundedContextsUseCase with repository dependency.

    Returns:
        Use case for listing bounded contexts
    """
    return ListBoundedContextsUseCase(get_bounded_context_repository())


def get_get_bounded_context_use_case() -> GetBoundedContextUseCase:
    """Get GetBoundedContextUseCase with repository dependency.

    Returns:
        Use case for getting a single bounded context
    """
    return GetBoundedContextUseCase(get_bounded_context_repository())


# =============================================================================
# Code Artifact Use Cases
# =============================================================================


def get_list_entities_use_case() -> ListEntitiesUseCase:
    """Get ListEntitiesUseCase with repository dependency.

    Returns:
        Use case for listing domain entities
    """
    return ListEntitiesUseCase(get_bounded_context_repository())


def get_list_use_cases_use_case() -> ListUseCasesUseCase:
    """Get ListUseCasesUseCase with repository dependency.

    Returns:
        Use case for listing use case classes
    """
    return ListUseCasesUseCase(get_bounded_context_repository())


def get_list_repository_protocols_use_case() -> ListRepositoryProtocolsUseCase:
    """Get ListRepositoryProtocolsUseCase with repository dependency.

    Returns:
        Use case for listing repository protocols
    """
    return ListRepositoryProtocolsUseCase(get_bounded_context_repository())


def get_list_service_protocols_use_case() -> ListServiceProtocolsUseCase:
    """Get ListServiceProtocolsUseCase with repository dependency.

    Returns:
        Use case for listing service protocols
    """
    return ListServiceProtocolsUseCase(get_bounded_context_repository())


def get_list_requests_use_case() -> ListRequestsUseCase:
    """Get ListRequestsUseCase with repository dependency.

    Returns:
        Use case for listing request DTOs
    """
    return ListRequestsUseCase(get_bounded_context_repository())


def get_list_responses_use_case() -> ListResponsesUseCase:
    """Get ListResponsesUseCase with repository dependency.

    Returns:
        Use case for listing response DTOs
    """
    return ListResponsesUseCase(get_bounded_context_repository())
