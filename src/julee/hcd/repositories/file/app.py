"""File-backed implementation of AppRepository."""

import logging
from pathlib import Path

from ...domain.models.app import App, AppType
from ...domain.repositories.app import AppRepository
from ...parsers.yaml import scan_app_manifests
from ...serializers.yaml import serialize_app
from julee.hcd.utils import normalize_name
from .base import FileRepositoryMixin

logger = logging.getLogger(__name__)


class FileAppRepository(FileRepositoryMixin[App], AppRepository):
    """File-backed implementation of AppRepository.

    Apps are stored as YAML manifests in the directory structure:
    {base_path}/{app_slug}/app.yaml
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize with base path for app manifests.

        Args:
            base_path: Root directory for app manifests (e.g., docs/apps/)
        """
        self.base_path = Path(base_path)
        self.storage: dict[str, App] = {}
        self.entity_name = "App"
        self.id_field = "slug"

        # Load existing apps from disk
        self._load_all()

    def _get_file_path(self, entity: App) -> Path:
        """Get file path for an app manifest."""
        return self.base_path / entity.slug / "app.yaml"

    def _serialize(self, entity: App) -> str:
        """Serialize app to YAML format."""
        return serialize_app(entity)

    def _load_all(self) -> None:
        """Load all apps from YAML manifests."""
        if not self.base_path.exists():
            logger.info(f"Apps directory not found: {self.base_path}")
            return

        apps = scan_app_manifests(self.base_path)
        for app in apps:
            self.storage[app.slug] = app

        logger.info(f"Loaded {len(self.storage)} apps from {self.base_path}")

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

    async def get_with_accelerator(self, accelerator_slug: str) -> list[App]:
        """Get apps that expose a specific accelerator."""
        return [
            app
            for app in self.storage.values()
            if accelerator_slug in (app.accelerators or [])
        ]
