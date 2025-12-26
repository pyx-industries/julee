"""List apps use case with co-located request/response."""

from pydantic import BaseModel, Field

from julee.core.decorators import use_case
from julee.hcd.entities.app import App
from julee.hcd.repositories.app import AppRepository


class ListAppsRequest(BaseModel):
    """Request for listing apps with optional filters.

    All filters are optional. When multiple filters are specified,
    they are combined with AND logic.
    """

    app_type: str | None = Field(
        default=None, description="Filter to apps of this type (staff, customers, vendors)"
    )
    has_accelerator: str | None = Field(
        default=None, description="Filter to apps exposing this accelerator"
    )


class ListAppsResponse(BaseModel):
    """Response from listing apps."""

    apps: list[App]

    @property
    def count(self) -> int:
        """Number of apps returned."""
        return len(self.apps)

    def grouped_by_type(self) -> dict[str, list[App]]:
        """Group apps by type."""
        result: dict[str, list[App]] = {}
        for app in self.apps:
            app_type = app.app_type.value if app.app_type else "unknown"
            result.setdefault(app_type, []).append(app)
        return result


@use_case
class ListAppsUseCase:
    """List apps with optional filtering.

    Supports filtering by app type and accelerator association.
    When no filters are provided, returns all apps.

    Examples:
        # All apps
        response = use_case.execute(ListAppsRequest())

        # Staff apps only
        response = use_case.execute(ListAppsRequest(app_type="staff"))

        # Apps exposing a specific accelerator
        response = use_case.execute(ListAppsRequest(has_accelerator="ceap"))
    """

    def __init__(self, app_repo: AppRepository) -> None:
        """Initialize with repository dependency.

        Args:
            app_repo: App repository instance
        """
        self.app_repo = app_repo

    async def execute(self, request: ListAppsRequest) -> ListAppsResponse:
        """List apps with optional filtering.

        Args:
            request: List request with optional type and accelerator filters

        Returns:
            Response containing filtered list of apps
        """
        apps = await self.app_repo.list_all()

        # Apply type filter
        if request.app_type:
            apps = [a for a in apps if a.matches_type(request.app_type)]

        # Apply accelerator filter
        if request.has_accelerator:
            apps = [
                a for a in apps
                if a.accelerators and request.has_accelerator in a.accelerators
            ]

        return ListAppsResponse(apps=apps)
