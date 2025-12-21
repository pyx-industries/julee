"""CreateContainerUseCase.

Use case for creating a new container.
"""

from ..requests import CreateContainerRequest
from ..responses import CreateContainerResponse
from ...repositories.container import ContainerRepository


class CreateContainerUseCase:
    """Use case for creating a container."""

    def __init__(self, container_repo: ContainerRepository) -> None:
        """Initialize with repository dependency.

        Args:
            container_repo: Container repository instance
        """
        self.container_repo = container_repo

    async def execute(self, request: CreateContainerRequest) -> CreateContainerResponse:
        """Create a new container.

        Args:
            request: Container creation request with data

        Returns:
            Response containing the created container
        """
        container = request.to_domain_model()
        await self.container_repo.save(container)
        return CreateContainerResponse(container=container)
