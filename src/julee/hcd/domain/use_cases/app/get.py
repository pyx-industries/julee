"""Get app use case with co-located request/response."""

from pydantic import BaseModel

from ...models.app import App
from ...repositories.app import AppRepository


class GetAppRequest(BaseModel):
    """Request for getting an app by slug."""

    slug: str


class GetAppResponse(BaseModel):
    """Response from getting an app."""

    app: App | None


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
