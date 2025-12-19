"""DeleteEpicUseCase.

Use case for deleting an epic.
"""

from .....hcd_api.requests import DeleteEpicRequest
from .....hcd_api.responses import DeleteEpicResponse
from ...repositories.epic import EpicRepository


class DeleteEpicUseCase:
    """Use case for deleting an epic."""

    def __init__(self, epic_repo: EpicRepository) -> None:
        """Initialize with repository dependency.

        Args:
            epic_repo: Epic repository instance
        """
        self.epic_repo = epic_repo

    async def execute(self, request: DeleteEpicRequest) -> DeleteEpicResponse:
        """Delete an epic by slug.

        Args:
            request: Delete request containing the epic slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.epic_repo.delete(request.slug)
        return DeleteEpicResponse(deleted=deleted)
