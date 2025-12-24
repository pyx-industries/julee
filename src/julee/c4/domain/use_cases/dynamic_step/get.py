"""Get dynamic step use case with co-located request/response."""

from pydantic import BaseModel

from ...models.dynamic_step import DynamicStep
from ...repositories.dynamic_step import DynamicStepRepository


class GetDynamicStepRequest(BaseModel):
    """Request for getting a dynamic step by slug."""

    slug: str


class GetDynamicStepResponse(BaseModel):
    """Response from getting a dynamic step."""

    dynamic_step: DynamicStep | None


class GetDynamicStepUseCase:
    """Use case for getting a dynamic step by slug.

    .. usecase-documentation:: julee.c4.domain.use_cases.dynamic_step.get:GetDynamicStepUseCase
    """

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
