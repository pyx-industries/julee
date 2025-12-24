"""Update accelerator use case with co-located request/response."""

from typing import Any

from pydantic import BaseModel

from julee.hcd.entities.accelerator import Accelerator
from julee.hcd.repositories.accelerator import AcceleratorRepository

from .create import IntegrationReferenceItem


class UpdateAcceleratorRequest(BaseModel):
    """Request for updating an accelerator."""

    slug: str
    status: str | None = None
    milestone: str | None = None
    acceptance: str | None = None
    objective: str | None = None
    sources_from: list[IntegrationReferenceItem] | None = None
    feeds_into: list[str] | None = None
    publishes_to: list[IntegrationReferenceItem] | None = None
    depends_on: list[str] | None = None

    def apply_to(self, existing: Accelerator) -> Accelerator:
        """Apply non-None fields to existing accelerator."""
        updates: dict[str, Any] = {}
        if self.status is not None:
            updates["status"] = self.status
        if self.milestone is not None:
            updates["milestone"] = self.milestone
        if self.acceptance is not None:
            updates["acceptance"] = self.acceptance
        if self.objective is not None:
            updates["objective"] = self.objective
        if self.sources_from is not None:
            updates["sources_from"] = [s.to_domain_model() for s in self.sources_from]
        if self.feeds_into is not None:
            updates["feeds_into"] = self.feeds_into
        if self.publishes_to is not None:
            updates["publishes_to"] = [p.to_domain_model() for p in self.publishes_to]
        if self.depends_on is not None:
            updates["depends_on"] = self.depends_on
        return existing.model_copy(update=updates) if updates else existing


class UpdateAcceleratorResponse(BaseModel):
    """Response from updating an accelerator."""

    accelerator: Accelerator | None
    found: bool = True


class UpdateAcceleratorUseCase:
    """Use case for updating an accelerator.

    .. usecase-documentation:: julee.hcd.domain.use_cases.accelerator.update:UpdateAcceleratorUseCase
    """

    def __init__(self, accelerator_repo: AcceleratorRepository) -> None:
        """Initialize with repository dependency.

        Args:
            accelerator_repo: Accelerator repository instance
        """
        self.accelerator_repo = accelerator_repo

    async def execute(
        self, request: UpdateAcceleratorRequest
    ) -> UpdateAcceleratorResponse:
        """Update an existing accelerator.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated accelerator if found
        """
        existing = await self.accelerator_repo.get(request.slug)
        if not existing:
            return UpdateAcceleratorResponse(accelerator=None, found=False)

        updated = request.apply_to(existing)
        await self.accelerator_repo.save(updated)
        return UpdateAcceleratorResponse(accelerator=updated, found=True)
