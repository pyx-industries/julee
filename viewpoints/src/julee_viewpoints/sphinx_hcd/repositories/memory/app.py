"""Memory implementation of AppRepository."""

import logging

from ...domain.models.app import App, AppType
from ...domain.repositories.app import AppRepository
from ...utils import normalize_name
from .base import MemoryRepositoryMixin

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
