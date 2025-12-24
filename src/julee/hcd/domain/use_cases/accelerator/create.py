"""CreateAcceleratorUseCase.

Use case for creating a new accelerator.
"""

from ...repositories.accelerator import AcceleratorRepository
from ..requests import CreateAcceleratorRequest
from ..responses import CreateAcceleratorResponse


class CreateAcceleratorUseCase:
    """Use case for creating an accelerator.

    .. usecase-documentation:: julee.hcd.domain.use_cases.accelerator.create:CreateAcceleratorUseCase
    """

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
