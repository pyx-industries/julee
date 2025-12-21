"""UpdateContainerUseCase.

Use case for updating an existing container.
"""

from ..requests import UpdateContainerRequest
from ..responses import UpdateContainerResponse
from ...repositories.container import ContainerRepository


class UpdateContainerUseCase:
    """Use case for updating a container."""

    def __init__(self, container_repo: ContainerRepository) -> None:
        """Initialize with repository dependency.

        Args:
            container_repo: Container repository instance
        """
        self.container_repo = container_repo

    async def execute(self, request: UpdateContainerRequest) -> UpdateContainerResponse:
        """Update an existing container.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated container if found
        """
        existing = await self.container_repo.get(request.slug)
        if not existing:
            return UpdateContainerResponse(container=None, found=False)

        updated = request.apply_to(existing)
        await self.container_repo.save(updated)
        return UpdateContainerResponse(container=updated, found=True)
