"""CreateAcceleratorUseCase.

Use case for creating a new accelerator.
"""

from .....hcd_api.requests import CreateAcceleratorRequest
from .....hcd_api.responses import CreateAcceleratorResponse
from ...repositories.accelerator import AcceleratorRepository


class CreateAcceleratorUseCase:
    """Use case for creating an accelerator."""

    def __init__(self, accelerator_repo: AcceleratorRepository) -> None:
        """Initialize with repository dependency.

        Args:
            accelerator_repo: Accelerator repository instance
        """
        self.accelerator_repo = accelerator_repo

    async def execute(
        self, request: CreateAcceleratorRequest
    ) -> CreateAcceleratorResponse:
        """Create a new accelerator.

        Args:
            request: Accelerator creation request with accelerator data

        Returns:
            Response containing the created accelerator
        """
        accelerator = request.to_domain_model()
        await self.accelerator_repo.save(accelerator)
        return CreateAcceleratorResponse(accelerator=accelerator)
