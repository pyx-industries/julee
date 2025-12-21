"""ListDynamicStepsUseCase.

Use case for listing all dynamic steps.
"""

from ..requests import ListDynamicStepsRequest
from ..responses import ListDynamicStepsResponse
from ...repositories.dynamic_step import DynamicStepRepository


class ListDynamicStepsUseCase:
    """Use case for listing all dynamic steps."""

    def __init__(self, dynamic_step_repo: DynamicStepRepository) -> None:
        """Initialize with repository dependency.

        Args:
            dynamic_step_repo: DynamicStep repository instance
        """
        self.dynamic_step_repo = dynamic_step_repo

    async def execute(
        self, request: ListDynamicStepsRequest
    ) -> ListDynamicStepsResponse:
        """List all dynamic steps.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all dynamic steps
        """
        dynamic_steps = await self.dynamic_step_repo.list_all()
        return ListDynamicStepsResponse(dynamic_steps=dynamic_steps)
