"""PipelineRouteResponseUseCase for pipeline routing.

Routes a response to zero or more downstream pipelines based on
declarative routing rules. Uses PipelineRouteRepository to find matching routes
and PipelineRequestTransformer to build appropriate requests.

This use case implements the multiplex routing pattern where a single
response can trigger multiple downstream pipelines.

See: docs/architecture/proposals/pipeline_router_design.md
"""

from pydantic import BaseModel, Field

from julee.shared.repositories.pipeline_route import PipelineRouteRepository
from julee.shared.services.pipeline_request_transformer import (
    PipelineRequestTransformer,
)


class PipelineRouteResponseRequest(BaseModel):
    """Request to route a response to downstream pipelines.

    Contains the serialized response and its type for route matching.
    """

    response: dict = Field(
        description="Serialized response object (from response.model_dump())"
    )
    response_type: str = Field(
        description="Response type name for route matching (FQN or class name)"
    )


# Backwards-compatible alias
RouteResponseRequest = PipelineRouteResponseRequest


class PipelineDispatch(BaseModel):
    """A pipeline to call with its request.

    Represents a single dispatch action: which pipeline to call
    and what request to send it.
    """

    pipeline: str = Field(description="Target pipeline name")
    request: dict = Field(description="Serialized request for the target pipeline")


class PipelineRouteResponseResponse(BaseModel):
    """Result of routing a response.

    Contains the list of dispatches to execute. May be empty if no
    routes matched the response.
    """

    dispatches: list[PipelineDispatch] = Field(
        default_factory=list, description="List of pipeline dispatches to execute"
    )


# Backwards-compatible alias
RouteResponseResponse = PipelineRouteResponseResponse


class PipelineRouteResponseUseCase:
    """Route a response to downstream pipelines.

    This use case:
    1. Looks up routes for the response type
    2. Evaluates conditions on each route
    3. Transforms responses to requests for matching routes
    4. Returns list of dispatches to execute

    The actual dispatch execution is done by the calling pipeline,
    not by this use case.
    """

    def __init__(
        self,
        route_repository: PipelineRouteRepository,
        request_transformer: PipelineRequestTransformer,
    ) -> None:
        """Initialize with dependencies.

        Args:
            route_repository: Repository for looking up routes
            request_transformer: Service for transforming responses to requests
        """
        self._route_repository = route_repository
        self._request_transformer = request_transformer

    async def execute(
        self, request: PipelineRouteResponseRequest
    ) -> PipelineRouteResponseResponse:
        """Route a response to downstream pipelines.

        Args:
            request: Contains serialized response and its type

        Returns:
            PipelineRouteResponseResponse with list of dispatches to execute.
            May be empty if no routes matched.
        """
        # Get routes for this response type
        routes = await self._route_repository.list_for_response_type(
            request.response_type
        )

        dispatches = []
        for route in routes:
            # Evaluate condition against the response dict
            if route.condition.evaluate(request.response):
                # Transform response to request
                transformed_request = self._request_transformer.transform(
                    route, request.response
                )
                dispatches.append(
                    PipelineDispatch(
                        pipeline=route.pipeline,
                        request=transformed_request.model_dump(),
                    )
                )

        return PipelineRouteResponseResponse(dispatches=dispatches)


# Backwards-compatible alias
RouteResponseUseCase = PipelineRouteResponseUseCase
