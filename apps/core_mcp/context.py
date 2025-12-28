"""Repository and use-case context for Core MCP tools.

Provides repository instances and use-case factories for MCP tool functions.
"""

import os
from functools import lru_cache
from pathlib import Path

from julee.core.infrastructure.repositories.file.solution_config import (
    FileSolutionConfigRepository,
)
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)

# Bounded context use cases
from julee.core.use_cases.bounded_context.get import GetBoundedContextUseCase
from julee.core.use_cases.bounded_context.list import ListBoundedContextsUseCase

# Code artifact use cases
from julee.core.use_cases.code_artifact.get_bounded_context_code import (
    GetBoundedContextCodeUseCase,
)
from julee.core.use_cases.code_artifact.list_entities import ListEntitiesUseCase
from julee.core.use_cases.code_artifact.list_pipelines import ListPipelinesUseCase
from julee.core.use_cases.code_artifact.list_repository_protocols import (
    ListRepositoryProtocolsUseCase,
)
from julee.core.use_cases.code_artifact.list_requests import ListRequestsUseCase
from julee.core.use_cases.code_artifact.list_responses import ListResponsesUseCase
from julee.core.use_cases.code_artifact.list_service_protocols import (
    ListServiceProtocolsUseCase,
)
from julee.core.use_cases.code_artifact.list_use_cases import ListUseCasesUseCase


def get_project_root() -> Path:
    """Get the project root directory from environment.

    Returns:
        Path to the project root directory for introspection
    """
    return Path(os.getenv("CORE_SOURCE_ROOT", ".")).resolve()


@lru_cache
def get_search_root() -> str:
    """Get the search_root from pyproject.toml config.

    Returns:
        The configured search_root path

    Raises:
        ValueError: If search_root is not configured
    """
    repo = FileSolutionConfigRepository()
    config = repo.get_policy_config_sync(get_project_root())
    if config.search_root is None:
        raise ValueError(
            "search_root not configured in [tool.julee] section of pyproject.toml. "
            'Add: search_root = "src/your_package"'
        )
    return config.search_root


# =============================================================================
# Repository Factories
# =============================================================================


@lru_cache
def get_bounded_context_repository() -> FilesystemBoundedContextRepository:
    """Get the bounded context repository singleton."""
    return FilesystemBoundedContextRepository(get_project_root(), get_search_root())


# =============================================================================
# Bounded Context Use-Case Factories
# =============================================================================


def get_get_bounded_context_use_case() -> GetBoundedContextUseCase:
    """Get GetBoundedContextUseCase with repository dependency."""
    return GetBoundedContextUseCase(get_bounded_context_repository())


def get_list_bounded_contexts_use_case() -> ListBoundedContextsUseCase:
    """Get ListBoundedContextsUseCase with repository dependency."""
    return ListBoundedContextsUseCase(get_bounded_context_repository())


# =============================================================================
# Code Artifact Use-Case Factories
# =============================================================================


def get_get_bounded_context_code_use_case() -> GetBoundedContextCodeUseCase:
    """Get GetBoundedContextCodeUseCase with repository dependency."""
    return GetBoundedContextCodeUseCase(get_bounded_context_repository())


def get_list_entities_use_case() -> ListEntitiesUseCase:
    """Get ListEntitiesUseCase with repository dependency."""
    return ListEntitiesUseCase(get_bounded_context_repository())


def get_list_pipelines_use_case() -> ListPipelinesUseCase:
    """Get ListPipelinesUseCase with repository dependency."""
    return ListPipelinesUseCase(get_bounded_context_repository())


def get_list_repository_protocols_use_case() -> ListRepositoryProtocolsUseCase:
    """Get ListRepositoryProtocolsUseCase with repository dependency."""
    return ListRepositoryProtocolsUseCase(get_bounded_context_repository())


def get_list_requests_use_case() -> ListRequestsUseCase:
    """Get ListRequestsUseCase with repository dependency."""
    return ListRequestsUseCase(get_bounded_context_repository())


def get_list_responses_use_case() -> ListResponsesUseCase:
    """Get ListResponsesUseCase with repository dependency."""
    return ListResponsesUseCase(get_bounded_context_repository())


def get_list_service_protocols_use_case() -> ListServiceProtocolsUseCase:
    """Get ListServiceProtocolsUseCase with repository dependency."""
    return ListServiceProtocolsUseCase(get_bounded_context_repository())


def get_list_use_cases_use_case() -> ListUseCasesUseCase:
    """Get ListUseCasesUseCase with repository dependency."""
    return ListUseCasesUseCase(get_bounded_context_repository())
