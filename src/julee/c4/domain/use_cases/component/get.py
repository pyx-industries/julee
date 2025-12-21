"""GetComponentUseCase.

Use case for getting a component by slug.
"""

from ..requests import GetComponentRequest
from ..responses import GetComponentResponse
from ...repositories.component import ComponentRepository


class GetComponentUseCase:
    """Use case for getting a component by slug."""

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
