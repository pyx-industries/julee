"""GetAcceleratorUseCase.

Use case for getting an accelerator by slug.
"""

from .....hcd_api.requests import GetAcceleratorRequest
from .....hcd_api.responses import GetAcceleratorResponse
from ...repositories.accelerator import AcceleratorRepository


class GetAcceleratorUseCase:
    """Use case for getting an accelerator by slug."""

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
