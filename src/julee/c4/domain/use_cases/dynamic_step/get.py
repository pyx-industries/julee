"""GetDynamicStepUseCase.

Use case for getting a dynamic step by slug.
"""

from ..requests import GetDynamicStepRequest
from ..responses import GetDynamicStepResponse
from ...repositories.dynamic_step import DynamicStepRepository


class GetDynamicStepUseCase:
    """Use case for getting a dynamic step by slug."""

    def __init__(self, dynamic_step_repo: DynamicStepRepository) -> None:
        """Initialize with repository dependency.

        Args:
            dynamic_step_repo: DynamicStep repository instance
        """
        self.dynamic_step_repo = dynamic_step_repo

    async def execute(self, request: GetDynamicStepRequest) -> GetDynamicStepResponse:
        """Get a dynamic step by slug.

        Args:
            request: Request containing the dynamic step slug

        Returns:
            Response containing the dynamic step if found, or None
        """
        dynamic_step = await self.dynamic_step_repo.get(request.slug)
        return GetDynamicStepResponse(dynamic_step=dynamic_step)
