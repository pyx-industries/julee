"""Memory implementation of ContribRepository."""

import logging

from julee.hcd.entities.contrib import ContribModule
from julee.hcd.repositories.contrib import ContribRepository
from julee.shared.repositories.memory.base import MemoryRepositoryMixin

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
