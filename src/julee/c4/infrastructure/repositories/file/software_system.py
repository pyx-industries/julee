"""File-backed SoftwareSystem repository implementation."""

import logging
from pathlib import Path

from julee.c4.entities.software_system import SoftwareSystem, SystemType
from julee.c4.parsers.rst import scan_software_system_directory
from julee.c4.repositories.software_system import SoftwareSystemRepository
from julee.c4.serializers.rst import serialize_software_system
from julee.c4.utils import normalize_name
from julee.core.infrastructure.repositories.file.base import FileRepositoryMixin

logger = logging.getLogger(__name__)


class FileSoftwareSystemRepository(
    FileRepositoryMixin[SoftwareSystem], SoftwareSystemRepository
):
    """File-backed implementation of SoftwareSystemRepository.

    Stores software systems as RST files with define-software-system directives.
    File structure: {base_path}/{slug}.rst
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize repository with base path.

        Args:
            base_path: Directory to store software system RST files
        """
        self.base_path = base_path
        self.storage: dict[str, SoftwareSystem] = {}
        self.entity_name = "SoftwareSystem"
        self.id_field = "slug"
        self._load_all()

    def _get_file_path(self, entity: SoftwareSystem) -> Path:
        """Get file path for a software system."""
        return self.base_path / f"{entity.slug}.rst"

    def _serialize(self, entity: SoftwareSystem) -> str:
        """Serialize software system to RST format."""
        return serialize_software_system(entity)

    def _load_all(self) -> None:
        """Load all software systems from disk."""
        if not self.base_path.exists():
            logger.debug(
                f"FileSoftwareSystemRepository: Base path does not exist: {self.base_path}"
            )
            return

        systems = scan_software_system_directory(self.base_path)
        for system in systems:
            self.storage[system.slug] = system

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
        to_remove = [slug for slug, s in self.storage.items() if s.docname == docname]
        for slug in to_remove:
            await self.delete(slug)
        return len(to_remove)
