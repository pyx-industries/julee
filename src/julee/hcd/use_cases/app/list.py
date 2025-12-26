"""List apps use case using FilterableListUseCase."""

from pydantic import BaseModel, Field

from julee.core.use_cases.generic_crud import (
    FilterableListUseCase,
    make_list_request,
)
from julee.hcd.entities.app import App
from julee.hcd.repositories.app import AppRepository

# Dynamic request from repository's list_filtered signature
ListAppsRequest = make_list_request("ListAppsRequest", AppRepository)


class ListAppsResponse(BaseModel):
    """Response from listing apps.

    Uses validation_alias to accept 'entities' from generic CRUD infrastructure
    while serializing as 'apps' for API consumers.
    """

    apps: list[App] = Field(default=[], validation_alias="entities")

    @property
    def entities(self) -> list[App]:
        """Alias for generic list operations."""
        return self.apps

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


class ListAppsUseCase(FilterableListUseCase[App, AppRepository]):
    """List apps with optional filtering.

    Filters are derived from AppRepository.list_filtered() signature:
    - app_type: Filter to apps of this type (staff, external, member-tool, etc.)

    Examples:
        # All apps
        response = use_case.execute(ListAppsRequest())

        # Staff apps only
        response = use_case.execute(ListAppsRequest(app_type="staff"))
    """

    response_cls = ListAppsResponse

    def __init__(self, app_repo: AppRepository) -> None:
        """Initialize with repository dependency."""
        super().__init__(app_repo)
