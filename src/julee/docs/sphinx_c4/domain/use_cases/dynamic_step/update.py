"""UpdateDynamicStepUseCase.

Use case for updating an existing dynamic step.
"""

from .....c4_api.requests import UpdateDynamicStepRequest
from .....c4_api.responses import UpdateDynamicStepResponse
from ...repositories.dynamic_step import DynamicStepRepository


class UpdateDynamicStepUseCase:
    """Use case for updating a dynamic step."""

    def __init__(self, dynamic_step_repo: DynamicStepRepository) -> None:
        """Initialize with repository dependency.

        Args:
            dynamic_step_repo: DynamicStep repository instance
        """
        self.dynamic_step_repo = dynamic_step_repo

    async def execute(self, request: UpdateDynamicStepRequest) -> UpdateDynamicStepResponse:
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
