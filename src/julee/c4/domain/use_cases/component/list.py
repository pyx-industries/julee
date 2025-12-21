"""ListComponentsUseCase.

Use case for listing all components.
"""

from ..requests import ListComponentsRequest
from ..responses import ListComponentsResponse
from ...repositories.component import ComponentRepository


class ListComponentsUseCase:
    """Use case for listing all components."""

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
