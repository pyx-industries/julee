"""List epics use case with co-located request/response."""

from pydantic import BaseModel, Field

from julee.core.decorators import use_case
from julee.hcd.entities.epic import Epic
from julee.hcd.repositories.epic import EpicRepository
from julee.hcd.utils import normalize_name


class ListEpicsRequest(BaseModel):
    """Request for listing epics with optional filters.

    All filters are optional. When multiple filters are specified,
    they are combined with AND logic.
    """

    has_stories: bool | None = Field(
        default=None, description="Filter to epics with/without story refs"
    )
    contains_story: str | None = Field(
        default=None, description="Filter to epics containing this story title"
    )


class ListEpicsResponse(BaseModel):
    """Response from listing epics."""

    epics: list[Epic]

    @property
    def count(self) -> int:
        """Number of epics returned."""
        return len(self.epics)

    @property
    def total_stories(self) -> int:
        """Total stories across all epics."""
        return sum(len(e.story_refs) for e in self.epics)


@use_case
class ListEpicsUseCase:
    """List epics with optional filtering.

    Supports filtering by story association. When no filters
    are provided, returns all epics.

    Examples:
        # All epics
        response = use_case.execute(ListEpicsRequest())

        # Epics that have stories
        response = use_case.execute(ListEpicsRequest(has_stories=True))

        # Epics containing a specific story
        response = use_case.execute(ListEpicsRequest(
            contains_story="Upload Scheme Documentation"
        ))
    """

    def __init__(self, epic_repo: EpicRepository) -> None:
        """Initialize with repository dependency.

        Args:
            epic_repo: Epic repository instance
        """
        self.epic_repo = epic_repo

    async def execute(self, request: ListEpicsRequest) -> ListEpicsResponse:
        """List epics with optional filtering.

        Args:
            request: List request with optional story filters

        Returns:
            Response containing filtered list of epics
        """
        epics = await self.epic_repo.list_all()

        # Apply has_stories filter
        if request.has_stories is True:
            epics = [e for e in epics if e.story_refs]
        elif request.has_stories is False:
            epics = [e for e in epics if not e.story_refs]

        # Apply contains_story filter
        if request.contains_story:
            story_normalized = normalize_name(request.contains_story)
            epics = [
                e
                for e in epics
                if any(
                    normalize_name(ref) == story_normalized for ref in e.story_refs
                )
            ]

        return ListEpicsResponse(epics=epics)
