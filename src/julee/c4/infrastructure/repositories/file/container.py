"""File-backed Container repository implementation."""

import logging
from pathlib import Path

from julee.c4.entities.container import Container, ContainerType
from julee.c4.parsers.rst import scan_container_directory
from julee.c4.repositories.container import ContainerRepository
from julee.c4.serializers.rst import serialize_container
from julee.core.infrastructure.repositories.file.base import FileRepositoryMixin

logger = logging.getLogger(__name__)


class FileContainerRepository(FileRepositoryMixin[Container], ContainerRepository):
    """File-backed implementation of ContainerRepository.

    Stores containers as RST files with define-container directives.
    File structure: {base_path}/{slug}.rst
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize repository with base path.

        Args:
            base_path: Directory to store container RST files
        """
        self.base_path = base_path
        self.storage: dict[str, Container] = {}
        self.entity_name = "Container"
        self.id_field = "slug"
        self._load_all()

    def _get_file_path(self, entity: Container) -> Path:
        """Get file path for a container."""
        return self.base_path / f"{entity.slug}.rst"

    def _serialize(self, entity: Container) -> str:
        """Serialize container to RST format."""
        return serialize_container(entity)

    def _load_all(self) -> None:
        """Load all containers from disk."""
        if not self.base_path.exists():
            logger.debug(
                f"FileContainerRepository: Base path does not exist: {self.base_path}"
            )
            return

        containers = scan_container_directory(self.base_path)
        for container in containers:
            self.storage[container.slug] = container

    async def get_by_system(self, system_slug: str) -> list[Container]:
        """Get all containers within a software system."""
        return [c for c in self.storage.values() if c.system_slug == system_slug]

    async def get_by_type(self, container_type: ContainerType) -> list[Container]:
        """Get containers of a specific type."""
        return [c for c in self.storage.values() if c.container_type == container_type]

    async def get_data_stores(self, system_slug: str | None = None) -> list[Container]:
        """Get all data store containers."""
        containers = [c for c in self.storage.values() if c.is_data_store]
        if system_slug:
            containers = [c for c in containers if c.system_slug == system_slug]
        return containers

    async def get_applications(self, system_slug: str | None = None) -> list[Container]:
        """Get all application containers (non-data-stores)."""
        containers = [c for c in self.storage.values() if c.is_application]
        if system_slug:
            containers = [c for c in containers if c.system_slug == system_slug]
        return containers

    async def get_by_tag(self, tag: str) -> list[Container]:
        """Get containers with a specific tag."""
        return [c for c in self.storage.values() if c.has_tag(tag)]

    async def get_by_docname(self, docname: str) -> list[Container]:
        """Get containers defined in a specific document."""
        return [c for c in self.storage.values() if c.docname == docname]

    async def clear_by_docname(self, docname: str) -> int:
        """Clear containers defined in a specific document."""
        to_remove = [slug for slug, c in self.storage.items() if c.docname == docname]
        for slug in to_remove:
            await self.delete(slug)
        return len(to_remove)
