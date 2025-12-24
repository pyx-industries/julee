"""Memory implementation of EpicRepository."""

import logging

from julee.hcd.entities.epic import Epic
from julee.hcd.utils import normalize_name

from ...domain.repositories.epic import EpicRepository
from .base import MemoryRepositoryMixin

logger = logging.getLogger(__name__)


class MemoryEpicRepository(MemoryRepositoryMixin[Epic], EpicRepository):
    """In-memory implementation of EpicRepository.

    Epics are stored in a dictionary keyed by slug. This implementation
    is used during Sphinx builds where epics are populated during doctree
    processing and support incremental builds via docname tracking.
    """

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.storage: dict[str, Epic] = {}
        self.entity_name = "Epic"
        self.id_field = "slug"

    async def get_by_docname(self, docname: str) -> list[Epic]:
        """Get all epics defined in a specific document."""
        return [epic for epic in self.storage.values() if epic.docname == docname]

    async def clear_by_docname(self, docname: str) -> int:
        """Remove all epics defined in a specific document."""
        to_remove = [
            slug for slug, epic in self.storage.items() if epic.docname == docname
        ]
        for slug in to_remove:
            del self.storage[slug]
        return len(to_remove)

    async def get_with_story_ref(self, story_title: str) -> list[Epic]:
        """Get epics that contain a specific story."""
        story_normalized = normalize_name(story_title)
        return [
            epic
            for epic in self.storage.values()
            if any(normalize_name(ref) == story_normalized for ref in epic.story_refs)
        ]

    async def get_all_story_refs(self) -> set[str]:
        """Get all unique story references across all epics."""
        refs: set[str] = set()
        for epic in self.storage.values():
            refs.update(normalize_name(ref) for ref in epic.story_refs)
        return refs
