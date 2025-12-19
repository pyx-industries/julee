"""File-backed SoftwareSystem repository implementation."""

import json
import logging
from pathlib import Path

from ...domain.models.software_system import SoftwareSystem, SystemType
from ...domain.repositories.software_system import SoftwareSystemRepository
from ...utils import normalize_name
from .base import FileRepositoryMixin

logger = logging.getLogger(__name__)


class FileSoftwareSystemRepository(
    FileRepositoryMixin[SoftwareSystem], SoftwareSystemRepository
):
    """File-backed implementation of SoftwareSystemRepository.

    Stores software systems as JSON files in the specified directory.
    File structure: {base_path}/{slug}.json
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize repository with base path.

        Args:
            base_path: Directory to store software system JSON files
        """
        self.base_path = base_path
        self.storage: dict[str, SoftwareSystem] = {}
        self.entity_name = "SoftwareSystem"
        self.id_field = "slug"
        self._load_all()

    def _get_file_path(self, entity: SoftwareSystem) -> Path:
        """Get file path for a software system."""
        return self.base_path / f"{entity.slug}.json"

    def _serialize(self, entity: SoftwareSystem) -> str:
        """Serialize software system to JSON."""
        return entity.model_dump_json(indent=2)

    def _load_all(self) -> None:
        """Load all software systems from disk."""
        if not self.base_path.exists():
            logger.debug(f"FileSoftwareSystemRepository: Base path does not exist: {self.base_path}")
            return

        for file_path in self.base_path.glob("*.json"):
            try:
                content = file_path.read_text(encoding="utf-8")
                data = json.loads(content)
                system = SoftwareSystem.model_validate(data)
                self.storage[system.slug] = system
                logger.debug(f"FileSoftwareSystemRepository: Loaded {system.slug}")
            except Exception as e:
                logger.warning(f"FileSoftwareSystemRepository: Failed to load {file_path}: {e}")

    async def get_by_type(self, system_type: SystemType) -> list[SoftwareSystem]:
        """Get all systems of a specific type."""
        return [s for s in self.storage.values() if s.system_type == system_type]

    async def get_internal_systems(self) -> list[SoftwareSystem]:
        """Get all internal (owned) systems."""
        return await self.get_by_type(SystemType.INTERNAL)

    async def get_external_systems(self) -> list[SoftwareSystem]:
        """Get all external systems."""
        return await self.get_by_type(SystemType.EXTERNAL)

    async def get_by_tag(self, tag: str) -> list[SoftwareSystem]:
        """Get systems with a specific tag."""
        return [s for s in self.storage.values() if s.has_tag(tag)]

    async def get_by_owner(self, owner: str) -> list[SoftwareSystem]:
        """Get systems owned by a specific team."""
        owner_normalized = normalize_name(owner)
        return [
            s
            for s in self.storage.values()
            if normalize_name(s.owner) == owner_normalized
        ]

    async def get_by_docname(self, docname: str) -> list[SoftwareSystem]:
        """Get systems defined in a specific document."""
        return [s for s in self.storage.values() if s.docname == docname]

    async def clear_by_docname(self, docname: str) -> int:
        """Clear systems defined in a specific document."""
        to_remove = [
            slug for slug, s in self.storage.items() if s.docname == docname
        ]
        for slug in to_remove:
            await self.delete(slug)
        return len(to_remove)
