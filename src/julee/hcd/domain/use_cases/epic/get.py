"""GetEpicUseCase.

Use case for getting an epic by slug.
"""

from ..requests import GetEpicRequest
from ..responses import GetEpicResponse
from ...repositories.epic import EpicRepository


class GetEpicUseCase:
    """Use case for getting an epic by slug."""

    def __init__(self, epic_repo: EpicRepository) -> None:
        """Initialize with repository dependency.

        Args:
            epic_repo: Epic repository instance
        """
        self.epic_repo = epic_repo

    async def execute(self, request: GetEpicRequest) -> GetEpicResponse:
        """Get an epic by slug.

        Args:
            request: Request containing the epic slug

        Returns:
            Response containing the epic if found, or None
        """
        epic = await self.epic_repo.get(request.slug)
        return GetEpicResponse(epic=epic)
