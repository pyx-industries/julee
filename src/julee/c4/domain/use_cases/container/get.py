"""Get container use case with co-located request/response."""

from pydantic import BaseModel

from ...models.container import Container
from ...repositories.container import ContainerRepository


class GetContainerRequest(BaseModel):
    """Request for getting a container by slug."""

    slug: str


class GetContainerResponse(BaseModel):
    """Response from getting a container."""

    container: Container | None


class GetContainerUseCase:
    """Use case for getting a container by slug.

    .. usecase-documentation:: julee.c4.domain.use_cases.container.get:GetContainerUseCase
    """

    def __init__(self, container_repo: ContainerRepository) -> None:
        """Initialize with repository dependency.

        Args:
            container_repo: Container repository instance
        """
        self.container_repo = container_repo

    async def execute(self, request: GetContainerRequest) -> GetContainerResponse:
        """Get a container by slug.

        Args:
            request: Request containing the container slug

        Returns:
            Response containing the container if found, or None
        """
        container = await self.container_repo.get(request.slug)
        return GetContainerResponse(container=container)
