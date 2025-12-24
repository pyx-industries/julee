"""List epics use case with co-located request/response."""

from pydantic import BaseModel

from julee.hcd.entities.epic import Epic
from julee.hcd.repositories.epic import EpicRepository


class ListEpicsRequest(BaseModel):
    """Request for listing epics."""

    pass


class ListEpicsResponse(BaseModel):
    """Response from listing epics."""

    epics: list[Epic]


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
