"""GetJourneyUseCase.

Use case for getting a journey by slug.
"""

from .....hcd_api.requests import GetJourneyRequest
from .....hcd_api.responses import GetJourneyResponse
from ...repositories.journey import JourneyRepository


class GetJourneyUseCase:
    """Use case for getting a journey by slug."""

    def __init__(self, journey_repo: JourneyRepository) -> None:
        """Initialize with repository dependency.

        Args:
            journey_repo: Journey repository instance
        """
        self.journey_repo = journey_repo

    async def execute(self, request: GetJourneyRequest) -> GetJourneyResponse:
        """Get a journey by slug.

        Args:
            request: Request containing the journey slug

        Returns:
            Response containing the journey if found, or None
        """
        journey = await self.journey_repo.get(request.slug)
        return GetJourneyResponse(journey=journey)
