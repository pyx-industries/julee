"""Update container use case with co-located request/response."""

from typing import Any

from pydantic import BaseModel

from julee.c4.entities.container import Container, ContainerType
from julee.c4.repositories.container import ContainerRepository


class UpdateContainerRequest(BaseModel):
    """Request for updating a container."""

    slug: str
    name: str | None = None
    system_slug: str | None = None
    description: str | None = None
    container_type: str | None = None
    technology: str | None = None
    url: str | None = None
    tags: list[str] | None = None

    def apply_to(self, existing: Container) -> Container:
        """Apply non-None fields to existing container."""
        updates: dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name
        if self.system_slug is not None:
            updates["system_slug"] = self.system_slug
        if self.description is not None:
            updates["description"] = self.description
        if self.container_type is not None:
            updates["container_type"] = ContainerType(self.container_type)
        if self.technology is not None:
            updates["technology"] = self.technology
        if self.url is not None:
            updates["url"] = self.url
        if self.tags is not None:
            updates["tags"] = self.tags
        return existing.model_copy(update=updates) if updates else existing


class UpdateContainerResponse(BaseModel):
    """Response from updating a container."""

    container: Container | None
    found: bool = True


class UpdateContainerUseCase:
    """Use case for updating a container.

    .. usecase-documentation:: julee.c4.domain.use_cases.container.update:UpdateContainerUseCase
    """

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
