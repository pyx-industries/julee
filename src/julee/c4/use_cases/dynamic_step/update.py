"""Update dynamic step use case with co-located request/response."""

from typing import Any

from pydantic import BaseModel

from julee.c4.entities.dynamic_step import DynamicStep
from julee.c4.repositories.dynamic_step import DynamicStepRepository


class UpdateDynamicStepRequest(BaseModel):
    """Request for updating a dynamic step."""

    slug: str
    step_number: int | None = None
    description: str | None = None
    technology: str | None = None
    return_description: str | None = None
    is_return: bool | None = None

    def apply_to(self, existing: DynamicStep) -> DynamicStep:
        """Apply non-None fields to existing dynamic step."""
        updates: dict[str, Any] = {}
        if self.step_number is not None:
            updates["step_number"] = self.step_number
        if self.description is not None:
            updates["description"] = self.description
        if self.technology is not None:
            updates["technology"] = self.technology
        if self.return_description is not None:
            updates["return_value"] = self.return_description
        if self.is_return is not None:
            updates["is_async"] = self.is_return
        return existing.model_copy(update=updates) if updates else existing


class UpdateDynamicStepResponse(BaseModel):
    """Response from updating a dynamic step."""

    dynamic_step: DynamicStep | None
    found: bool = True


class UpdateDynamicStepUseCase:
    """Use case for updating a dynamic step.

    .. usecase-documentation:: julee.c4.domain.use_cases.dynamic_step.update:UpdateDynamicStepUseCase
    """

    def __init__(self, dynamic_step_repo: DynamicStepRepository) -> None:
        """Initialize with repository dependency.

        Args:
            dynamic_step_repo: DynamicStep repository instance
        """
        self.dynamic_step_repo = dynamic_step_repo

    async def execute(
        self, request: UpdateDynamicStepRequest
    ) -> UpdateDynamicStepResponse:
        """Update an existing dynamic step.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated dynamic step if found
        """
        existing = await self.dynamic_step_repo.get(request.slug)
        if not existing:
            return UpdateDynamicStepResponse(dynamic_step=None, found=False)

        updated = request.apply_to(existing)
        await self.dynamic_step_repo.save(updated)
        return UpdateDynamicStepResponse(dynamic_step=updated, found=True)
