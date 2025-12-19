"""File-backed Component repository implementation."""

import json
import logging
from pathlib import Path

from ...domain.models.component import Component
from ...domain.repositories.component import ComponentRepository
from .base import FileRepositoryMixin

logger = logging.getLogger(__name__)


class FileComponentRepository(
    FileRepositoryMixin[Component], ComponentRepository
):
    """File-backed implementation of ComponentRepository.

    Stores components as JSON files in the specified directory.
    File structure: {base_path}/{slug}.json
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize repository with base path.

        Args:
            base_path: Directory to store component JSON files
        """
        self.base_path = base_path
        self.storage: dict[str, Component] = {}
        self.entity_name = "Component"
        self.id_field = "slug"
        self._load_all()

    def _get_file_path(self, entity: Component) -> Path:
        """Get file path for a component."""
        return self.base_path / f"{entity.slug}.json"

    def _serialize(self, entity: Component) -> str:
        """Serialize component to JSON."""
        return entity.model_dump_json(indent=2)

    def _load_all(self) -> None:
        """Load all components from disk."""
        if not self.base_path.exists():
            logger.debug(f"FileComponentRepository: Base path does not exist: {self.base_path}")
            return

        for file_path in self.base_path.glob("*.json"):
            try:
                content = file_path.read_text(encoding="utf-8")
                data = json.loads(content)
                component = Component.model_validate(data)
                self.storage[component.slug] = component
                logger.debug(f"FileComponentRepository: Loaded {component.slug}")
            except Exception as e:
                logger.warning(f"FileComponentRepository: Failed to load {file_path}: {e}")

    async def get_by_container(self, container_slug: str) -> list[Component]:
        """Get all components within a container."""
        return [
            c for c in self.storage.values() if c.container_slug == container_slug
        ]

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
        to_remove = [
            slug for slug, c in self.storage.items() if c.docname == docname
        ]
        for slug in to_remove:
            await self.delete(slug)
        return len(to_remove)
