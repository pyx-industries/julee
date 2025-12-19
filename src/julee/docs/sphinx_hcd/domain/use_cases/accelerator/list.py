"""ListAcceleratorsUseCase.

Use case for listing all accelerators.
"""

from .....hcd_api.requests import ListAcceleratorsRequest
from .....hcd_api.responses import ListAcceleratorsResponse
from ...repositories.accelerator import AcceleratorRepository


class ListAcceleratorsUseCase:
    """Use case for listing all accelerators."""

    def __init__(self, accelerator_repo: AcceleratorRepository) -> None:
        """Initialize with repository dependency.

        Args:
            accelerator_repo: Accelerator repository instance
        """
        self.accelerator_repo = accelerator_repo

    async def execute(
        self, request: ListAcceleratorsRequest
    ) -> ListAcceleratorsResponse:
        """List all accelerators.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all accelerators
        """
        accelerators = await self.accelerator_repo.list_all()
        return ListAcceleratorsResponse(accelerators=accelerators)
