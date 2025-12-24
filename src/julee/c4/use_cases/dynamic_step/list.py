"""List dynamic steps use case with co-located request/response."""

from pydantic import BaseModel

from julee.c4.entities.dynamic_step import DynamicStep
from julee.c4.repositories.dynamic_step import DynamicStepRepository


class ListDynamicStepsRequest(BaseModel):
    """Request for listing dynamic steps."""

    pass


class ListDynamicStepsResponse(BaseModel):
    """Response from listing dynamic steps."""

    dynamic_steps: list[DynamicStep]


class ListDynamicStepsUseCase:
    """Use case for listing all dynamic steps.

    .. usecase-documentation:: julee.c4.domain.use_cases.dynamic_step.list:ListDynamicStepsUseCase
    """

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
