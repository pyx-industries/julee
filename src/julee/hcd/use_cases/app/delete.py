"""Delete app use case with co-located request/response."""

from pydantic import BaseModel

from julee.hcd.repositories.app import AppRepository


class DeleteAppRequest(BaseModel):
    """Request for deleting an app by slug."""

    slug: str


class DeleteAppResponse(BaseModel):
    """Response from deleting an app."""

    deleted: bool


class DeleteAppUseCase:
    """Use case for deleting an app.

    .. usecase-documentation:: julee.hcd.domain.use_cases.app.delete:DeleteAppUseCase
    """

    def __init__(self, app_repo: AppRepository) -> None:
        """Initialize with repository dependency.

        Args:
            app_repo: App repository instance
        """
        self.app_repo = app_repo

    async def execute(self, request: DeleteAppRequest) -> DeleteAppResponse:
        """Delete an app by slug.

        Args:
            request: Delete request containing the app slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.app_repo.delete(request.slug)
        return DeleteAppResponse(deleted=deleted)
