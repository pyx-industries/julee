"""CreateDynamicStepUseCase.

Use case for creating a new dynamic step.
"""

from .....c4_api.requests import CreateDynamicStepRequest
from .....c4_api.responses import CreateDynamicStepResponse
from ...repositories.dynamic_step import DynamicStepRepository


class CreateDynamicStepUseCase:
    """Use case for creating a dynamic step."""

    def __init__(self, dynamic_step_repo: DynamicStepRepository) -> None:
        """Initialize with repository dependency.

        Args:
            dynamic_step_repo: DynamicStep repository instance
        """
        self.dynamic_step_repo = dynamic_step_repo

    async def execute(self, request: CreateDynamicStepRequest) -> CreateDynamicStepResponse:
        """Create a new dynamic step.

        Args:
            request: Dynamic step creation request with data

        Returns:
            Response containing the created dynamic step
        """
        dynamic_step = request.to_domain_model()
        await self.dynamic_step_repo.save(dynamic_step)
        return CreateDynamicStepResponse(dynamic_step=dynamic_step)
