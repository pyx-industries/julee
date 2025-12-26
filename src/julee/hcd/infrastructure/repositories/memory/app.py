"""Memory implementation of AppRepository."""

import logging

from julee.core.infrastructure.repositories.memory.base import MemoryRepositoryMixin
from julee.hcd.entities.app import App, AppType
from julee.hcd.repositories.app import AppRepository
from julee.hcd.utils import normalize_name

logger = logging.getLogger(__name__)


class MemoryAppRepository(MemoryRepositoryMixin[App], AppRepository):
    """In-memory implementation of AppRepository.

    Apps are stored in a dictionary keyed by slug. This implementation
    is used during Sphinx builds where apps are populated at builder-inited
    and queried during doctree processing.
    """

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.storage: dict[str, App] = {}
        self.entity_name = "App"
        self.id_field = "slug"

    # -------------------------------------------------------------------------
    # BaseRepository implementation (delegating to protected helpers)
    # -------------------------------------------------------------------------

    async def get(self, entity_id: str) -> App | None:
        """Get an app by slug."""
        return self._get_entity(entity_id)

    async def get_many(self, entity_ids: list[str]) -> dict[str, App | None]:
        """Get multiple apps by slug."""
        return self._get_many_entities(entity_ids)

    async def save(self, entity: App) -> None:
        """Save an app."""
        self._save_entity(entity)

    async def list_all(self) -> list[App]:
        """List all apps."""
        return self._list_all_entities()

    async def delete(self, entity_id: str) -> bool:
        """Delete an app by slug."""
        return self._delete_entity(entity_id)

    async def clear(self) -> None:
        """Clear all apps."""
        self._clear_storage()

    # -------------------------------------------------------------------------
    # AppRepository-specific queries
    # -------------------------------------------------------------------------

    async def get_by_type(self, app_type: AppType) -> list[App]:
        """Get all apps of a specific type."""
        return [app for app in self.storage.values() if app.app_type == app_type]

    async def get_by_name(self, name: str) -> App | None:
        """Get an app by its display name (case-insensitive)."""
        name_normalized = normalize_name(name)
        for app in self.storage.values():
            if app.name_normalized == name_normalized:
                return app
        return None

    async def get_all_types(self) -> set[AppType]:
        """Get all unique app types that have apps."""
        return {app.app_type for app in self.storage.values()}

    async def get_apps_with_accelerators(self) -> list[App]:
        """Get all apps that have accelerators defined."""
        return [app for app in self.storage.values() if app.accelerators]

    async def list_slugs(self) -> set[str]:
        """List all app slugs."""
        return self._list_slugs()

    async def get_by_accelerator(self, accelerator_slug: str) -> list[App]:
        """Get all apps that reference a specific accelerator."""
        return [
            app for app in self.storage.values() if accelerator_slug in app.accelerators
        ]
