"""Get journey use case with co-located request/response."""

from pydantic import BaseModel

from julee.hcd.entities.journey import Journey
from julee.hcd.repositories.journey import JourneyRepository


class GetJourneyRequest(BaseModel):
    """Request for getting a journey by slug."""

    slug: str


class GetJourneyResponse(BaseModel):
    """Response from getting a journey."""

    journey: Journey | None


class GetJourneyUseCase:
    """Use case for getting a journey by slug.

    .. usecase-documentation:: julee.hcd.domain.use_cases.journey.get:GetJourneyUseCase
    """

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
