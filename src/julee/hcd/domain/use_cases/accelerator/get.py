"""GetAcceleratorUseCase.

Use case for getting an accelerator by slug.
"""

from ...repositories.accelerator import AcceleratorRepository
from ..requests import GetAcceleratorRequest
from ..responses import GetAcceleratorResponse


class GetAcceleratorUseCase:
    """Use case for getting an accelerator by slug.

    .. usecase-documentation:: julee.hcd.domain.use_cases.accelerator.get:GetAcceleratorUseCase
    """

    def __init__(self, accelerator_repo: AcceleratorRepository) -> None:
        """Initialize with repository dependency.

        Args:
            accelerator_repo: Accelerator repository instance
        """
        self.accelerator_repo = accelerator_repo

    async def execute(self, request: GetAcceleratorRequest) -> GetAcceleratorResponse:
        """Get an accelerator by slug.

        Args:
            request: Request containing the accelerator slug

        Returns:
            Response containing the accelerator if found, or None
        """
        accelerator = await self.accelerator_repo.get(request.slug)
        return GetAcceleratorResponse(accelerator=accelerator)
