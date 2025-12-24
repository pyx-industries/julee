"""CreateComponentUseCase.

Use case for creating a new component.
"""

from ...repositories.component import ComponentRepository
from ..requests import CreateComponentRequest
from ..responses import CreateComponentResponse


class CreateComponentUseCase:
    """Use case for creating a component.

    .. usecase-documentation:: julee.c4.domain.use_cases.component.create:CreateComponentUseCase
    """

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
