"""Delete accelerator use case with co-located request/response."""

from pydantic import BaseModel

from ...repositories.accelerator import AcceleratorRepository


class DeleteAcceleratorRequest(BaseModel):
    """Request for deleting an accelerator by slug."""

    slug: str


class DeleteAcceleratorResponse(BaseModel):
    """Response from deleting an accelerator."""

    deleted: bool


class DeleteAcceleratorUseCase:
    """Use case for deleting an accelerator.

    .. usecase-documentation:: julee.hcd.domain.use_cases.accelerator.delete:DeleteAcceleratorUseCase
    """

    def __init__(self, accelerator_repo: AcceleratorRepository) -> None:
        """Initialize with repository dependency.

        Args:
            accelerator_repo: Accelerator repository instance
        """
        self.accelerator_repo = accelerator_repo

    async def execute(
        self, request: DeleteAcceleratorRequest
    ) -> DeleteAcceleratorResponse:
        """Delete an accelerator by slug.

        Args:
            request: Delete request containing the accelerator slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.accelerator_repo.delete(request.slug)
        return DeleteAcceleratorResponse(deleted=deleted)
