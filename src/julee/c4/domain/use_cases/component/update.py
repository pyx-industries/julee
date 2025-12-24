"""Update component use case with co-located request/response."""

from typing import Any

from pydantic import BaseModel

from ...models.component import Component
from ...repositories.component import ComponentRepository


class UpdateComponentRequest(BaseModel):
    """Request for updating a component."""

    slug: str
    name: str | None = None
    container_slug: str | None = None
    system_slug: str | None = None
    description: str | None = None
    technology: str | None = None
    interface: str | None = None
    code_path: str | None = None
    url: str | None = None
    tags: list[str] | None = None

    def apply_to(self, existing: Component) -> Component:
        """Apply non-None fields to existing component."""
        updates: dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name
        if self.container_slug is not None:
            updates["container_slug"] = self.container_slug
        if self.system_slug is not None:
            updates["system_slug"] = self.system_slug
        if self.description is not None:
            updates["description"] = self.description
        if self.technology is not None:
            updates["technology"] = self.technology
        if self.interface is not None:
            updates["interface"] = self.interface
        if self.code_path is not None:
            updates["code_path"] = self.code_path
        if self.url is not None:
            updates["url"] = self.url
        if self.tags is not None:
            updates["tags"] = self.tags
        return existing.model_copy(update=updates) if updates else existing


class UpdateComponentResponse(BaseModel):
    """Response from updating a component."""

    component: Component | None
    found: bool = True


class UpdateComponentUseCase:
    """Use case for updating a component.

    .. usecase-documentation:: julee.c4.domain.use_cases.component.update:UpdateComponentUseCase
    """

    def __init__(self, component_repo: ComponentRepository) -> None:
        """Initialize with repository dependency.

        Args:
            component_repo: Component repository instance
        """
        self.component_repo = component_repo

    async def execute(self, request: UpdateComponentRequest) -> UpdateComponentResponse:
        """Update an existing component.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated component if found
        """
        existing = await self.component_repo.get(request.slug)
        if not existing:
            return UpdateComponentResponse(component=None, found=False)

        updated = request.apply_to(existing)
        await self.component_repo.save(updated)
        return UpdateComponentResponse(component=updated, found=True)
