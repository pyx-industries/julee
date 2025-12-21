"""ListContainersUseCase.

Use case for listing all containers.
"""

from ...repositories.container import ContainerRepository
from ..requests import ListContainersRequest
from ..responses import ListContainersResponse


class ListContainersUseCase:
    """Use case for listing all containers."""

    def __init__(self, container_repo: ContainerRepository) -> None:
        """Initialize with repository dependency.

        Args:
            container_repo: Container repository instance
        """
        self.container_repo = container_repo

    async def execute(self, request: ListContainersRequest) -> ListContainersResponse:
        """List all containers.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all containers
        """
        containers = await self.container_repo.list_all()
        return ListContainersResponse(containers=containers)
