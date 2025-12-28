"""ListPipelineRoutesUseCase with co-located request/response.

Use case for listing pipeline routes with optional filtering.
"""

from pydantic import BaseModel

from julee.core.decorators import use_case
from julee.core.entities.pipeline_route import PipelineRoute
from julee.core.repositories.pipeline_route import PipelineRouteRepository


class ListPipelineRoutesRequest(BaseModel):
    """Request for listing pipeline routes.

    Optionally filter by response type.
    """

    response_type: str | None = None


class ListPipelineRoutesResponse(BaseModel):
    """Response from listing pipeline routes."""

    routes: list[PipelineRoute]


@use_case
class ListPipelineRoutesUseCase:
    """Use case for listing pipeline routes.

    Returns all routes or routes filtered by response type.
    """

    def __init__(self, route_repo: PipelineRouteRepository) -> None:
        """Initialize with repository dependency.

        Args:
            route_repo: Repository for accessing pipeline routes
        """
        self.route_repo = route_repo

    async def execute(
        self, request: ListPipelineRoutesRequest
    ) -> ListPipelineRoutesResponse:
        """List pipeline routes.

        Args:
            request: List request with optional response_type filter

        Returns:
            Response containing list of matching routes
        """
        if request.response_type:
            routes = await self.route_repo.list_for_response_type(request.response_type)
        else:
            routes = await self.route_repo.list_all()
        return ListPipelineRoutesResponse(routes=routes)
