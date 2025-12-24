"""UpdateSoftwareSystemUseCase with co-located request/response.

Use case for updating an existing software system.
"""

from typing import Any

from pydantic import BaseModel

from ...models.software_system import SoftwareSystem, SystemType
from ...repositories.software_system import SoftwareSystemRepository


class UpdateSoftwareSystemRequest(BaseModel):
    """Request for updating a software system."""

    slug: str
    name: str | None = None
    description: str | None = None
    system_type: str | None = None
    owner: str | None = None
    technology: str | None = None
    url: str | None = None
    tags: list[str] | None = None

    def apply_to(self, existing: SoftwareSystem) -> SoftwareSystem:
        """Apply non-None fields to existing software system."""
        updates: dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name
        if self.description is not None:
            updates["description"] = self.description
        if self.system_type is not None:
            updates["system_type"] = SystemType(self.system_type)
        if self.owner is not None:
            updates["owner"] = self.owner
        if self.technology is not None:
            updates["technology"] = self.technology
        if self.url is not None:
            updates["url"] = self.url
        if self.tags is not None:
            updates["tags"] = self.tags
        return existing.model_copy(update=updates) if updates else existing


class UpdateSoftwareSystemResponse(BaseModel):
    """Response from updating a software system."""

    software_system: SoftwareSystem | None
    found: bool = True


class UpdateSoftwareSystemUseCase:
    """Use case for updating a software system.

    .. usecase-documentation:: julee.c4.domain.use_cases.software_system.update:UpdateSoftwareSystemUseCase
    """

    def __init__(self, software_system_repo: SoftwareSystemRepository) -> None:
        """Initialize with repository dependency.

        Args:
            software_system_repo: SoftwareSystem repository instance
        """
        self.software_system_repo = software_system_repo

    async def execute(
        self, request: UpdateSoftwareSystemRequest
    ) -> UpdateSoftwareSystemResponse:
        """Update an existing software system.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated software system if found
        """
        existing = await self.software_system_repo.get(request.slug)
        if not existing:
            return UpdateSoftwareSystemResponse(software_system=None, found=False)

        updated = request.apply_to(existing)
        await self.software_system_repo.save(updated)
        return UpdateSoftwareSystemResponse(software_system=updated, found=True)
