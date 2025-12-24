"""UpdateJourneyUseCase.

Use case for updating an existing journey.
"""

from ...repositories.journey import JourneyRepository
from ..requests import UpdateJourneyRequest
from ..responses import UpdateJourneyResponse


class UpdateJourneyUseCase:
    """Use case for updating a journey.

    .. usecase-documentation:: julee.hcd.domain.use_cases.journey.update:UpdateJourneyUseCase
    """

    def __init__(self, journey_repo: JourneyRepository) -> None:
        """Initialize with repository dependency.

        Args:
            journey_repo: Journey repository instance
        """
        self.journey_repo = journey_repo

    async def execute(self, request: UpdateJourneyRequest) -> UpdateJourneyResponse:
        """Update an existing journey.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated journey if found
        """
        existing = await self.journey_repo.get(request.slug)
        if not existing:
            return UpdateJourneyResponse(journey=None, found=False)

        updated = request.apply_to(existing)
        await self.journey_repo.save(updated)
        return UpdateJourneyResponse(journey=updated, found=True)
