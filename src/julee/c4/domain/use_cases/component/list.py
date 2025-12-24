"""List components use case with co-located request/response."""

from pydantic import BaseModel

from ...models.component import Component
from ...repositories.component import ComponentRepository


class ListComponentsRequest(BaseModel):
    """Request for listing components."""

    pass


class ListComponentsResponse(BaseModel):
    """Response from listing components."""

    components: list[Component]


class ListComponentsUseCase:
    """Use case for listing all components.

    .. usecase-documentation:: julee.c4.domain.use_cases.component.list:ListComponentsUseCase
    """

    def __init__(self, component_repo: ComponentRepository) -> None:
        """Initialize with repository dependency.

        Args:
            component_repo: Component repository instance
        """
        self.component_repo = component_repo

    async def execute(self, request: ListComponentsRequest) -> ListComponentsResponse:
        """List all components.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all components
        """
        components = await self.component_repo.list_all()
        return ListComponentsResponse(components=components)
