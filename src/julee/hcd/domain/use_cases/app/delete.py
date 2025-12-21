"""DeleteAppUseCase.

Use case for deleting an app.
"""

from ...repositories.app import AppRepository
from ..requests import DeleteAppRequest
from ..responses import DeleteAppResponse


class DeleteAppUseCase:
    """Use case for deleting an app."""

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
