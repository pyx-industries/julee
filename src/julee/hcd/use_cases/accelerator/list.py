"""List accelerators use case with co-located request/response."""

from pydantic import BaseModel

from julee.hcd.entities.accelerator import Accelerator
from julee.hcd.repositories.accelerator import AcceleratorRepository


class ListAcceleratorsRequest(BaseModel):
    """Request for listing accelerators."""

    pass


class ListAcceleratorsResponse(BaseModel):
    """Response from listing accelerators."""

    accelerators: list[Accelerator]


class ListAcceleratorsUseCase:
    """Use case for listing all accelerators.

    .. usecase-documentation:: julee.hcd.domain.use_cases.accelerator.list:ListAcceleratorsUseCase
    """

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
