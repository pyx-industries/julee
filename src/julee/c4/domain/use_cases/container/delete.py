"""DeleteContainerUseCase.

Use case for deleting a container.
"""

from ...repositories.container import ContainerRepository
from ..requests import DeleteContainerRequest
from ..responses import DeleteContainerResponse


class DeleteContainerUseCase:
    """Use case for deleting a container.

    .. usecase-documentation:: julee.c4.domain.use_cases.container.delete:DeleteContainerUseCase
    """

    def __init__(self, container_repo: ContainerRepository) -> None:
        """Initialize with repository dependency.

        Args:
            container_repo: Container repository instance
        """
        self.container_repo = container_repo

    async def execute(self, request: DeleteContainerRequest) -> DeleteContainerResponse:
        """Delete a container by slug.

        Args:
            request: Delete request containing the container slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.container_repo.delete(request.slug)
        return DeleteContainerResponse(deleted=deleted)
