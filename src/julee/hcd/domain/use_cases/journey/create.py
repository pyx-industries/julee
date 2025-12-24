"""CreateJourneyUseCase.

Use case for creating a new journey.
"""

from ...repositories.journey import JourneyRepository
from ..requests import CreateJourneyRequest
from ..responses import CreateJourneyResponse


class CreateJourneyUseCase:
    """Use case for creating a journey.

    .. usecase-documentation:: julee.hcd.domain.use_cases.journey.create:CreateJourneyUseCase
    """

    def __init__(self, journey_repo: JourneyRepository) -> None:
        """Initialize with repository dependency.

        Args:
            journey_repo: Journey repository instance
        """
        self.journey_repo = journey_repo

    async def execute(self, request: CreateJourneyRequest) -> CreateJourneyResponse:
        """Create a new journey.

        Args:
            request: Journey creation request with journey data

        Returns:
            Response containing the created journey
        """
        journey = request.to_domain_model()
        await self.journey_repo.save(journey)
        return CreateJourneyResponse(journey=journey)
