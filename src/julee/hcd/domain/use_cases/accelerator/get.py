"""Get accelerator use case with co-located request/response."""

from pydantic import BaseModel

from ...models.accelerator import Accelerator
from ...repositories.accelerator import AcceleratorRepository


class GetAcceleratorRequest(BaseModel):
    """Request for getting an accelerator by slug."""

    slug: str


class GetAcceleratorResponse(BaseModel):
    """Response from getting an accelerator."""

    accelerator: Accelerator | None


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
