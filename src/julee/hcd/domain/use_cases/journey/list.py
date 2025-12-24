"""ListJourneysUseCase.

Use case for listing all journeys.
"""

from ...repositories.journey import JourneyRepository
from ..requests import ListJourneysRequest
from ..responses import ListJourneysResponse


class ListJourneysUseCase:
    """Use case for listing all journeys.

    .. usecase-documentation:: julee.hcd.domain.use_cases.journey.list:ListJourneysUseCase
    """

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
