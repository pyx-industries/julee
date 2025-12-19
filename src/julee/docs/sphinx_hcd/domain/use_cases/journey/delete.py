"""DeleteJourneyUseCase.

Use case for deleting a journey.
"""

from .....hcd_api.requests import DeleteJourneyRequest
from .....hcd_api.responses import DeleteJourneyResponse
from ...repositories.journey import JourneyRepository


class DeleteJourneyUseCase:
    """Use case for deleting a journey."""

    def __init__(self, journey_repo: JourneyRepository) -> None:
        """Initialize with repository dependency.

        Args:
            journey_repo: Journey repository instance
        """
        self.journey_repo = journey_repo

    async def execute(self, request: DeleteJourneyRequest) -> DeleteJourneyResponse:
        """Delete a journey by slug.

        Args:
            request: Delete request containing the journey slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.journey_repo.delete(request.slug)
        return DeleteJourneyResponse(deleted=deleted)
