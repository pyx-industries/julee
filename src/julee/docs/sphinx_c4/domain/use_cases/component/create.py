"""CreateComponentUseCase.

Use case for creating a new component.
"""

from .....c4_api.requests import CreateComponentRequest
from .....c4_api.responses import CreateComponentResponse
from ...repositories.component import ComponentRepository


class CreateComponentUseCase:
    """Use case for creating a component."""

    def __init__(self, component_repo: ComponentRepository) -> None:
        """Initialize with repository dependency.

        Args:
            component_repo: Component repository instance
        """
        self.component_repo = component_repo

    async def execute(self, request: CreateComponentRequest) -> CreateComponentResponse:
        """Create a new component.

        Args:
            request: Component creation request with data

        Returns:
            Response containing the created component
        """
        component = request.to_domain_model()
        await self.component_repo.save(component)
        return CreateComponentResponse(component=component)
