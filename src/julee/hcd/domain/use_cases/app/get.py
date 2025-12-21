"""GetAppUseCase.

Use case for getting an app by slug.
"""

from ..requests import GetAppRequest
from ..responses import GetAppResponse
from ...repositories.app import AppRepository


class GetAppUseCase:
    """Use case for getting an app by slug."""

    def __init__(self, app_repo: AppRepository) -> None:
        """Initialize with repository dependency.

        Args:
            app_repo: App repository instance
        """
        self.app_repo = app_repo

    async def execute(self, request: GetAppRequest) -> GetAppResponse:
        """Get an app by slug.

        Args:
            request: Request containing the app slug

        Returns:
            Response containing the app if found, or None
        """
        app = await self.app_repo.get(request.slug)
        return GetAppResponse(app=app)
