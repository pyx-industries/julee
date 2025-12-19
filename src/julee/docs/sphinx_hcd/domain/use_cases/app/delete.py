"""DeleteAppUseCase.

Use case for deleting an app.
"""

from .....hcd_api.requests import DeleteAppRequest
from .....hcd_api.responses import DeleteAppResponse
from ...repositories.app import AppRepository


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
