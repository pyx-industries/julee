"""Delete epic use case with co-located request/response."""

from pydantic import BaseModel

from julee.hcd.repositories.epic import EpicRepository


class DeleteEpicRequest(BaseModel):
    """Request for deleting an epic by slug."""

    slug: str


class DeleteEpicResponse(BaseModel):
    """Response from deleting an epic."""

    deleted: bool


class DeleteEpicUseCase:
    """Use case for deleting an epic.

    .. usecase-documentation:: julee.hcd.domain.use_cases.epic.delete:DeleteEpicUseCase
    """

    def __init__(self, epic_repo: EpicRepository) -> None:
        """Initialize with repository dependency.

        Args:
            epic_repo: Epic repository instance
        """
        self.epic_repo = epic_repo

    async def execute(self, request: DeleteEpicRequest) -> DeleteEpicResponse:
        """Delete an epic by slug.

        Args:
            request: Delete request containing the epic slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.epic_repo.delete(request.slug)
        return DeleteEpicResponse(deleted=deleted)
