"""In-memory Container repository implementation."""

from ...domain.models.container import Container, ContainerType
from ...domain.repositories.container import ContainerRepository
from .base import MemoryRepositoryMixin


class MemoryContainerRepository(
    MemoryRepositoryMixin[Container], ContainerRepository
):
    """In-memory implementation of ContainerRepository.

    Stores containers in a dictionary keyed by slug.
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        self.storage: dict[str, Container] = {}
        self.entity_name = "Container"
        self.id_field = "slug"

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
        to_remove = [
            slug for slug, c in self.storage.items() if c.docname == docname
        ]
        for slug in to_remove:
            del self.storage[slug]
        return len(to_remove)
