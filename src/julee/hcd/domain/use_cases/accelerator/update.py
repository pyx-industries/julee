"""UpdateAcceleratorUseCase.

Use case for updating an existing accelerator.
"""

from ...repositories.accelerator import AcceleratorRepository
from ..requests import UpdateAcceleratorRequest
from ..responses import UpdateAcceleratorResponse


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
