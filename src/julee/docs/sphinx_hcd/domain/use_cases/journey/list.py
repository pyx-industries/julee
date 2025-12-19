"""ListJourneysUseCase.

Use case for listing all journeys.
"""

from .....hcd_api.requests import ListJourneysRequest
from .....hcd_api.responses import ListJourneysResponse
from ...repositories.journey import JourneyRepository


class ListJourneysUseCase:
    """Use case for listing all journeys."""

    def __init__(self, journey_repo: JourneyRepository) -> None:
        """Initialize with repository dependency.

        Args:
            journey_repo: Journey repository instance
        """
        self.journey_repo = journey_repo

    async def execute(self, request: ListJourneysRequest) -> ListJourneysResponse:
        """List all journeys.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all journeys
        """
        journeys = await self.journey_repo.list_all()
        return ListJourneysResponse(journeys=journeys)
