"""File-backed Component repository implementation."""

import logging
from pathlib import Path

from julee.c4.entities.component import Component
from julee.c4.parsers.rst import scan_component_directory
from julee.c4.repositories.component import ComponentRepository
from julee.c4.serializers.rst import serialize_component
from julee.shared.infrastructure.repositories.file.base import FileRepositoryMixin

logger = logging.getLogger(__name__)


class FileComponentRepository(FileRepositoryMixin[Component], ComponentRepository):
    """File-backed implementation of ComponentRepository.

    Stores components as RST files with define-component directives.
    File structure: {base_path}/{slug}.rst
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize repository with base path.

        Args:
            base_path: Directory to store component RST files
        """
        self.base_path = base_path
        self.storage: dict[str, Component] = {}
        self.entity_name = "Component"
        self.id_field = "slug"
        self._load_all()

    def _get_file_path(self, entity: Component) -> Path:
        """Get file path for a component."""
        return self.base_path / f"{entity.slug}.rst"

    def _serialize(self, entity: Component) -> str:
        """Serialize component to RST format."""
        return serialize_component(entity)

    def _load_all(self) -> None:
        """Load all components from disk."""
        if not self.base_path.exists():
            logger.debug(
                f"FileComponentRepository: Base path does not exist: {self.base_path}"
            )
            return

        components = scan_component_directory(self.base_path)
        for component in components:
            self.storage[component.slug] = component

    async def get_by_container(self, container_slug: str) -> list[Component]:
        """Get all components within a container."""
        return [c for c in self.storage.values() if c.container_slug == container_slug]

    async def get_by_system(self, system_slug: str) -> list[Component]:
        """Get all components within a software system."""
        return [c for c in self.storage.values() if c.system_slug == system_slug]

    async def get_with_code(self) -> list[Component]:
        """Get components that have linked code paths."""
        return [c for c in self.storage.values() if c.has_code]

    async def get_by_tag(self, tag: str) -> list[Component]:
        """Get components with a specific tag."""
        return [c for c in self.storage.values() if c.has_tag(tag)]

    async def get_by_docname(self, docname: str) -> list[Component]:
        """Get components defined in a specific document."""
        return [c for c in self.storage.values() if c.docname == docname]

    async def clear_by_docname(self, docname: str) -> int:
        """Clear components defined in a specific document."""
        to_remove = [slug for slug, c in self.storage.items() if c.docname == docname]
        for slug in to_remove:
            await self.delete(slug)
        return len(to_remove)
