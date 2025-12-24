"""Delete journey use case with co-located request/response."""

from pydantic import BaseModel

from ...repositories.journey import JourneyRepository


class DeleteJourneyRequest(BaseModel):
    """Request for deleting a journey by slug."""

    slug: str


class DeleteJourneyResponse(BaseModel):
    """Response from deleting a journey."""

    deleted: bool


class DeleteJourneyUseCase:
    """Use case for deleting a journey.

    .. usecase-documentation:: julee.hcd.domain.use_cases.journey.delete:DeleteJourneyUseCase
    """

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
