"""ListAppsUseCase.

Use case for listing all apps.
"""

from ...repositories.app import AppRepository
from ..requests import ListAppsRequest
from ..responses import ListAppsResponse


class ListAppsUseCase:
    """Use case for listing all apps.

    .. usecase-documentation:: julee.hcd.domain.use_cases.app.list:ListAppsUseCase
    """

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
