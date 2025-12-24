"""GetAppUseCase.

Use case for getting an app by slug.
"""

from ...repositories.app import AppRepository
from ..requests import GetAppRequest
from ..responses import GetAppResponse


class GetAppUseCase:
    """Use case for getting an app by slug.

    .. usecase-documentation:: julee.hcd.domain.use_cases.app.get:GetAppUseCase
    """

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
