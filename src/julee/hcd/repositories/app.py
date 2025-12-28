"""AppRepository protocol.

Defines the interface for app data access.
"""

from typing import Protocol, runtime_checkable

from julee.core.repositories.base import BaseRepository
from julee.hcd.entities.app import App, AppType


@runtime_checkable
class AppRepository(BaseRepository[App], Protocol):
    """Repository protocol for App entities.

    Extends BaseRepository with app-specific query methods.
    Apps are indexed from YAML manifests and are read-only during
    a Sphinx build (populated at builder-inited, queried during rendering).
    """

    async def get_by_type(self, app_type: AppType) -> list[App]:
        """Get all apps of a specific type.

        Args:
            app_type: Application type to filter by

        Returns:
            List of apps matching the type
        """
        ...

    async def get_by_name(self, name: str) -> App | None:
        """Get an app by its display name (case-insensitive).

        Args:
            name: Display name to search for

        Returns:
            App if found, None otherwise
        """
        ...

    async def get_all_types(self) -> set[AppType]:
        """Get all unique app types that have apps.

        Returns:
            Set of app types with at least one app
        """
        ...

    async def get_apps_with_accelerators(self) -> list[App]:
        """Get all apps that have accelerators defined.

        Returns:
            List of apps with non-empty accelerators list
        """
        ...

    async def get_by_accelerator(self, accelerator_slug: str) -> list[App]:
        """Get all apps that reference a specific accelerator.

        Args:
            accelerator_slug: Accelerator slug to search for

        Returns:
            List of apps that have this accelerator in their accelerators list
        """
        ...

    async def list_filtered(
        self,
        solution_slug: str | None = None,
        app_type: str | None = None,
        has_accelerator: str | None = None,
    ) -> list[App]:
        """List apps matching filters.

        Filter parameters declared here are automatically surfaced as
        FastAPI query params via make_list_request(). Implementations
        should use AND logic when multiple filters are provided.

        Args:
            solution_slug: Filter to apps for this solution
            app_type: Filter to apps of this type (staff, external, member-tool, etc.)
            has_accelerator: Filter to apps that expose this accelerator

        Returns:
            List of apps matching all provided filters
        """
        ...
