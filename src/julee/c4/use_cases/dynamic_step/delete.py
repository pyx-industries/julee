"""Delete dynamic step use case with co-located request/response."""

from pydantic import BaseModel

from julee.c4.repositories.dynamic_step import DynamicStepRepository


class DeleteDynamicStepRequest(BaseModel):
    """Request for deleting a dynamic step by slug."""

    slug: str


class DeleteDynamicStepResponse(BaseModel):
    """Response from deleting a dynamic step."""

    deleted: bool


class DeleteDynamicStepUseCase:
    """Use case for deleting a dynamic step.

    .. usecase-documentation:: julee.c4.domain.use_cases.dynamic_step.delete:DeleteDynamicStepUseCase
    """

    def __init__(self, dynamic_step_repo: DynamicStepRepository) -> None:
        """Initialize with repository dependency.

        Args:
            dynamic_step_repo: DynamicStep repository instance
        """
        self.dynamic_step_repo = dynamic_step_repo

    async def execute(
        self, request: DeleteDynamicStepRequest
    ) -> DeleteDynamicStepResponse:
        """Delete a dynamic step by slug.

        Args:
            request: Delete request containing the dynamic step slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.dynamic_step_repo.delete(request.slug)
        return DeleteDynamicStepResponse(deleted=deleted)
