"""Use cases for the shared (core) accelerator.

These use cases operate on the foundational code concepts.
"""

from julee.shared.domain.use_cases.bounded_context import (
    GetBoundedContextUseCase,
    ListBoundedContextsUseCase,
)
from julee.shared.domain.use_cases.code_artifact import (
    ListEntitiesUseCase,
    ListPipelinesUseCase,
    ListRepositoryProtocolsUseCase,
    ListRequestsUseCase,
    ListResponsesUseCase,
    ListServiceProtocolsUseCase,
    ListUseCasesUseCase,
)
from julee.shared.domain.use_cases.requests import (
    GetBoundedContextRequest,
    GetCodeArtifactRequest,
    ListBoundedContextsRequest,
    ListCodeArtifactsRequest,
)
from julee.shared.domain.use_cases.responses import (
    CodeArtifactWithContext,
    GetBoundedContextResponse,
    GetCodeArtifactResponse,
    ListBoundedContextsResponse,
    ListCodeArtifactsResponse,
    ListPipelinesResponse,
)

__all__ = [
    # Bounded context use cases
    "GetBoundedContextUseCase",
    "GetBoundedContextRequest",
    "GetBoundedContextResponse",
    "ListBoundedContextsUseCase",
    "ListBoundedContextsRequest",
    "ListBoundedContextsResponse",
    # Code artifact use cases
    "ListEntitiesUseCase",
    "ListPipelinesUseCase",
    "ListRepositoryProtocolsUseCase",
    "ListRequestsUseCase",
    "ListResponsesUseCase",
    "ListServiceProtocolsUseCase",
    "ListUseCasesUseCase",
    "ListCodeArtifactsRequest",
    "ListCodeArtifactsResponse",
    "ListPipelinesResponse",
    "CodeArtifactWithContext",
    "GetCodeArtifactRequest",
    "GetCodeArtifactResponse",
]
