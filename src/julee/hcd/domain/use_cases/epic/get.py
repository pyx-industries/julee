"""Get epic use case with co-located request/response."""

from pydantic import BaseModel

from ...models.epic import Epic
from ...repositories.epic import EpicRepository


class GetEpicRequest(BaseModel):
    """Request for getting an epic by slug."""

    slug: str


class GetEpicResponse(BaseModel):
    """Response from getting an epic."""

    epic: Epic | None


class GetEpicUseCase:
    """Use case for getting an epic by slug.

    .. usecase-documentation:: julee.hcd.domain.use_cases.epic.get:GetEpicUseCase
    """

    def __init__(self, epic_repo: EpicRepository) -> None:
        """Initialize with repository dependency.

        Args:
            epic_repo: Epic repository instance
        """
        self.epic_repo = epic_repo

    async def execute(self, request: GetEpicRequest) -> GetEpicResponse:
        """Get an epic by slug.

        Args:
            request: Request containing the epic slug

        Returns:
            Response containing the epic if found, or None
        """
        epic = await self.epic_repo.get(request.slug)
        return GetEpicResponse(epic=epic)
