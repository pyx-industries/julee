"""ListAppsUseCase.

Use case for listing all apps.
"""

from .....hcd_api.requests import ListAppsRequest
from .....hcd_api.responses import ListAppsResponse
from ...repositories.app import AppRepository


class ListAppsUseCase:
    """Use case for listing all apps."""

    def __init__(self, app_repo: AppRepository) -> None:
        """Initialize with repository dependency.

        Args:
            app_repo: App repository instance
        """
        self.app_repo = app_repo

    async def execute(self, request: ListAppsRequest) -> ListAppsResponse:
        """List all apps.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all apps
        """
        apps = await self.app_repo.list_all()
        return ListAppsResponse(apps=apps)
