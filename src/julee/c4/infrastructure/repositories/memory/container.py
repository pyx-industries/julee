"""In-memory Container repository implementation."""

from julee.c4.entities.container import Container, ContainerType
from julee.c4.repositories.container import ContainerRepository
from julee.core.infrastructure.repositories.memory.base import MemoryRepositoryMixin


class MemoryContainerRepository(MemoryRepositoryMixin[Container], ContainerRepository):
    """In-memory implementation of ContainerRepository.

    Stores containers in a dictionary keyed by slug.
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        self.storage: dict[str, Container] = {}
        self.entity_name = "Container"
        self.id_field = "slug"

    # -------------------------------------------------------------------------
    # BaseRepository implementation (delegating to protected helpers)
    # -------------------------------------------------------------------------

    async def get(self, entity_id: str) -> Container | None:
        """Get a container by slug."""
        return self._get_entity(entity_id)

    async def get_many(self, entity_ids: list[str]) -> dict[str, Container | None]:
        """Get multiple containers by slug."""
        return self._get_many_entities(entity_ids)

    async def save(self, entity: Container) -> None:
        """Save a container."""
        self._save_entity(entity)

    async def list_all(self) -> list[Container]:
        """List all containers."""
        return self._list_all_entities()

    async def delete(self, entity_id: str) -> bool:
        """Delete a container by slug."""
        return self._delete_entity(entity_id)

    async def clear(self) -> None:
        """Clear all containers."""
        self._clear_storage()

    # -------------------------------------------------------------------------
    # ContainerRepository-specific queries
    # -------------------------------------------------------------------------

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
            del self.storage[slug]
        return len(to_remove)
