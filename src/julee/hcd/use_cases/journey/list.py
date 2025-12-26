"""List journeys use case with co-located request/response."""

from pydantic import BaseModel, Field

from julee.core.decorators import use_case
from julee.hcd.entities.journey import Journey
from julee.hcd.repositories.journey import JourneyRepository
from julee.hcd.utils import normalize_name


class ListJourneysRequest(BaseModel):
    """Request for listing journeys with optional filters.

    All filters are optional. When multiple filters are specified,
    they are combined with AND logic.
    """

    contains_story: str | None = Field(
        default=None, description="Filter to journeys containing this story title"
    )


class ListJourneysResponse(BaseModel):
    """Response from listing journeys."""

    journeys: list[Journey]

    @property
    def count(self) -> int:
        """Number of journeys returned."""
        return len(self.journeys)


@use_case
class ListJourneysUseCase:
    """List journeys with optional filtering.

    Supports filtering by story association. When no filters
    are provided, returns all journeys.

    Examples:
        # All journeys
        response = use_case.execute(ListJourneysRequest())

        # Journeys containing a specific story
        response = use_case.execute(ListJourneysRequest(
            contains_story="Upload Scheme Documentation"
        ))
    """

    def __init__(self, journey_repo: JourneyRepository) -> None:
        """Initialize with repository dependency.

        Args:
            journey_repo: Journey repository instance
        """
        self.journey_repo = journey_repo

    async def execute(self, request: ListJourneysRequest) -> ListJourneysResponse:
        """List journeys with optional filtering.

        Args:
            request: List request with optional story filter

        Returns:
            Response containing filtered list of journeys
        """
        journeys = await self.journey_repo.list_all()

        # Apply contains_story filter
        if request.contains_story:
            story_normalized = normalize_name(request.contains_story)
            journeys = [
                j for j in journeys
                if any(
                    step.is_story and normalize_name(step.ref) == story_normalized
                    for step in j.steps
                )
            ]

        return ListJourneysResponse(journeys=journeys)
