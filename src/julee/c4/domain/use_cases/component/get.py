"""Get component use case with co-located request/response."""

from pydantic import BaseModel

from ...models.component import Component
from ...repositories.component import ComponentRepository


class GetComponentRequest(BaseModel):
    """Request for getting a component by slug."""

    slug: str


class GetComponentResponse(BaseModel):
    """Response from getting a component."""

    component: Component | None


class GetComponentUseCase:
    """Use case for getting a component by slug.

    .. usecase-documentation:: julee.c4.domain.use_cases.component.get:GetComponentUseCase
    """

    def __init__(self, component_repo: ComponentRepository) -> None:
        """Initialize with repository dependency.

        Args:
            component_repo: Component repository instance
        """
        self.component_repo = component_repo

    async def execute(self, request: GetComponentRequest) -> GetComponentResponse:
        """Get a component by slug.

        Args:
            request: Request containing the component slug

        Returns:
            Response containing the component if found, or None
        """
        component = await self.component_repo.get(request.slug)
        return GetComponentResponse(component=component)
