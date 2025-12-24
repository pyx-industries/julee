"""List apps use case with co-located request/response."""

from pydantic import BaseModel

from julee.hcd.entities.app import App

from ...repositories.app import AppRepository


class ListAppsRequest(BaseModel):
    """Request for listing apps."""

    pass


class ListAppsResponse(BaseModel):
    """Response from listing apps."""

    apps: list[App]


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
