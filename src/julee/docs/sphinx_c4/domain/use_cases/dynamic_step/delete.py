"""DeleteDynamicStepUseCase.

Use case for deleting a dynamic step.
"""

from .....c4_api.requests import DeleteDynamicStepRequest
from .....c4_api.responses import DeleteDynamicStepResponse
from ...repositories.dynamic_step import DynamicStepRepository


class DeleteDynamicStepUseCase:
    """Use case for deleting a dynamic step."""

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
