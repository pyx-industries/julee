"""DeleteAcceleratorUseCase.

Use case for deleting an accelerator.
"""

from .....hcd_api.requests import DeleteAcceleratorRequest
from .....hcd_api.responses import DeleteAcceleratorResponse
from ...repositories.accelerator import AcceleratorRepository


class DeleteAcceleratorUseCase:
    """Use case for deleting an accelerator."""

    def __init__(self, accelerator_repo: AcceleratorRepository) -> None:
        """Initialize with repository dependency.

        Args:
            accelerator_repo: Accelerator repository instance
        """
        self.accelerator_repo = accelerator_repo

    async def execute(self, request: DeleteAcceleratorRequest) -> DeleteAcceleratorResponse:
        """Delete an accelerator by slug.

        Args:
            request: Delete request containing the accelerator slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.accelerator_repo.delete(request.slug)
        return DeleteAcceleratorResponse(deleted=deleted)
