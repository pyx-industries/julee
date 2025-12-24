"""File-backed implementation of IntegrationRepository."""

import logging
from pathlib import Path

from julee.hcd.entities.integration import Direction, Integration
from julee.hcd.parsers.yaml import scan_integration_manifests
from julee.hcd.repositories.integration import IntegrationRepository
from julee.hcd.serializers.yaml import serialize_integration
from julee.hcd.utils import normalize_name

from .base import FileRepositoryMixin

logger = logging.getLogger(__name__)


class FileIntegrationRepository(
    FileRepositoryMixin[Integration], IntegrationRepository
):
    """File-backed implementation of IntegrationRepository.

    Integrations are stored as YAML manifests in the directory structure:
    {base_path}/{module_name}/integration.yaml
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize with base path for integration manifests.

        Args:
            base_path: Root directory for integration manifests (e.g., docs/integrations/)
        """
        self.base_path = Path(base_path)
        self.storage: dict[str, Integration] = {}
        self.entity_name = "Integration"
        self.id_field = "slug"

        # Load existing integrations from disk
        self._load_all()

    def _get_file_path(self, entity: Integration) -> Path:
        """Get file path for an integration manifest."""
        return self.base_path / entity.module / "integration.yaml"

    def _serialize(self, entity: Integration) -> str:
        """Serialize integration to YAML format."""
        return serialize_integration(entity)

    def _load_all(self) -> None:
        """Load all integrations from YAML manifests."""
        if not self.base_path.exists():
            logger.info(f"Integrations directory not found: {self.base_path}")
            return

        integrations = scan_integration_manifests(self.base_path)
        for integration in integrations:
            self.storage[integration.slug] = integration

        logger.info(f"Loaded {len(self.storage)} integrations from {self.base_path}")

    async def get_by_direction(self, direction: Direction) -> list[Integration]:
        """Get all integrations with a specific direction."""
        return [
            integration
            for integration in self.storage.values()
            if integration.direction == direction
        ]

    async def get_by_name(self, name: str) -> Integration | None:
        """Get an integration by its display name (case-insensitive)."""
        name_normalized = normalize_name(name)
        for integration in self.storage.values():
            if integration.name_normalized == name_normalized:
                return integration
        return None

    async def get_by_module(self, module: str) -> Integration | None:
        """Get an integration by its module name."""
        for integration in self.storage.values():
            if integration.module == module:
                return integration
        return None
