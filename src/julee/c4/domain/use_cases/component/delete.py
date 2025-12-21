"""DeleteComponentUseCase.

Use case for deleting a component.
"""

from ...repositories.component import ComponentRepository
from ..requests import DeleteComponentRequest
from ..responses import DeleteComponentResponse


class DeleteComponentUseCase:
    """Use case for deleting a component."""

    def __init__(self, component_repo: ComponentRepository) -> None:
        """Initialize with repository dependency.

        Args:
            component_repo: Component repository instance
        """
        self.component_repo = component_repo

    async def execute(self, request: DeleteComponentRequest) -> DeleteComponentResponse:
        """Delete a component by slug.

        Args:
            request: Delete request containing the component slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.component_repo.delete(request.slug)
        return DeleteComponentResponse(deleted=deleted)
