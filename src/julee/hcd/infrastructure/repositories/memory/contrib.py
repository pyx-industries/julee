"""Memory implementation of ContribRepository."""

import logging

from julee.core.infrastructure.repositories.memory.base import MemoryRepositoryMixin
from julee.hcd.entities.contrib import ContribModule
from julee.hcd.repositories.contrib import ContribRepository

logger = logging.getLogger(__name__)


class MemoryContribRepository(MemoryRepositoryMixin[ContribModule], ContribRepository):
    """In-memory implementation of ContribRepository.

    Contrib modules are stored in a dictionary keyed by slug. This implementation
    is used during Sphinx builds where contrib modules are populated during doctree
    processing and support incremental builds via docname tracking.
    """

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.storage: dict[str, ContribModule] = {}
        self.entity_name = "ContribModule"
        self.id_field = "slug"

    # -------------------------------------------------------------------------
    # BaseRepository implementation (delegating to protected helpers)
    # -------------------------------------------------------------------------

    async def get(self, entity_id: str) -> ContribModule | None:
        """Get a contrib module by slug."""
        return self._get_entity(entity_id)

    async def get_many(self, entity_ids: list[str]) -> dict[str, ContribModule | None]:
        """Get multiple contrib modules by slug."""
        return self._get_many_entities(entity_ids)

    async def save(self, entity: ContribModule) -> None:
        """Save a contrib module."""
        self._save_entity(entity)

    async def list_all(self) -> list[ContribModule]:
        """List all contrib modules."""
        return self._list_all_entities()

    async def delete(self, entity_id: str) -> bool:
        """Delete a contrib module by slug."""
        return self._delete_entity(entity_id)

    async def clear(self) -> None:
        """Clear all contrib modules."""
        self._clear_storage()

    # -------------------------------------------------------------------------
    # ContribRepository-specific queries
    # -------------------------------------------------------------------------

    async def get_by_docname(self, docname: str) -> list[ContribModule]:
        """Get all contrib modules defined in a specific document."""
        return [
            contrib for contrib in self.storage.values() if contrib.docname == docname
        ]

    async def clear_by_docname(self, docname: str) -> int:
        """Remove all contrib modules defined in a specific document."""
        to_remove = [
            slug for slug, contrib in self.storage.items() if contrib.docname == docname
        ]
        for slug in to_remove:
            del self.storage[slug]
        return len(to_remove)
