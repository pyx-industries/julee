"""ListEpicsUseCase.

Use case for listing all epics.
"""

from ...repositories.epic import EpicRepository
from ..requests import ListEpicsRequest
from ..responses import ListEpicsResponse


class ListEpicsUseCase:
    """Use case for listing all epics.

    .. usecase-documentation:: julee.hcd.domain.use_cases.epic.list:ListEpicsUseCase
    """

    def __init__(self, epic_repo: EpicRepository) -> None:
        """Initialize with repository dependency.

        Args:
            epic_repo: Epic repository instance
        """
        self.epic_repo = epic_repo

    async def execute(self, request: ListEpicsRequest) -> ListEpicsResponse:
        """List all epics.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all epics
        """
        epics = await self.epic_repo.list_all()
        return ListEpicsResponse(epics=epics)
