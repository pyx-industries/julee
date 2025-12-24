"""Use cases for the shared (core) accelerator.

These use cases operate on the foundational code concepts.
"""

from julee.core.use_cases.bounded_context import (
    GetBoundedContextRequest,
    GetBoundedContextResponse,
    GetBoundedContextUseCase,
    ListBoundedContextsRequest,
    ListBoundedContextsResponse,
    ListBoundedContextsUseCase,
)
from julee.core.use_cases.code_artifact import (
    CodeArtifactWithContext,
    ListCodeArtifactsRequest,
    ListCodeArtifactsResponse,
    ListEntitiesUseCase,
    ListPipelinesResponse,
    ListPipelinesUseCase,
    ListRepositoryProtocolsUseCase,
    ListRequestsUseCase,
    ListResponsesUseCase,
    ListServiceProtocolsUseCase,
    ListUseCasesUseCase,
)
from julee.core.use_cases.pipeline_route_response import (
    PipelineDispatch,
    PipelineRouteResponseRequest,
    PipelineRouteResponseResponse,
    PipelineRouteResponseUseCase,
    RouteResponseRequest,
    RouteResponseResponse,
    RouteResponseUseCase,
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
    "CodeArtifactWithContext",
    "ListCodeArtifactsRequest",
    "ListCodeArtifactsResponse",
    "ListEntitiesUseCase",
    "ListPipelinesResponse",
    "ListPipelinesUseCase",
    "ListRepositoryProtocolsUseCase",
    "ListRequestsUseCase",
    "ListResponsesUseCase",
    "ListServiceProtocolsUseCase",
    "ListUseCasesUseCase",
    # Route response use case
    "PipelineDispatch",
    "PipelineRouteResponseRequest",
    "PipelineRouteResponseResponse",
    "PipelineRouteResponseUseCase",
    "RouteResponseRequest",
    "RouteResponseResponse",
    "RouteResponseUseCase",
]
