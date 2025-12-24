"""List containers use case with co-located request/response."""

from pydantic import BaseModel

from ...models.container import Container
from ...repositories.container import ContainerRepository


class ListContainersRequest(BaseModel):
    """Request for listing containers."""

    pass


class ListContainersResponse(BaseModel):
    """Response from listing containers."""

    containers: list[Container]


class ListContainersUseCase:
    """Use case for listing all containers.

    .. usecase-documentation:: julee.c4.domain.use_cases.container.list:ListContainersUseCase
    """

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
