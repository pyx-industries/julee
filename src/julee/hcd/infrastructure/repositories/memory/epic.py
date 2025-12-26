"""Memory implementation of EpicRepository."""

import logging

from julee.core.infrastructure.repositories.memory.base import MemoryRepositoryMixin
from julee.hcd.entities.epic import Epic
from julee.hcd.repositories.epic import EpicRepository
from julee.hcd.utils import normalize_name

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

    # -------------------------------------------------------------------------
    # BaseRepository implementation (delegating to protected helpers)
    # -------------------------------------------------------------------------

    async def get(self, entity_id: str) -> Epic | None:
        """Get an epic by slug."""
        return self._get_entity(entity_id)

    async def get_many(self, entity_ids: list[str]) -> dict[str, Epic | None]:
        """Get multiple epics by slug."""
        return self._get_many_entities(entity_ids)

    async def save(self, entity: Epic) -> None:
        """Save an epic."""
        self._save_entity(entity)

    async def list_all(self) -> list[Epic]:
        """List all epics."""
        return self._list_all_entities()

    async def delete(self, entity_id: str) -> bool:
        """Delete an epic by slug."""
        return self._delete_entity(entity_id)

    async def clear(self) -> None:
        """Clear all epics."""
        self._clear_storage()

    # -------------------------------------------------------------------------
    # EpicRepository-specific queries
    # -------------------------------------------------------------------------

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

    async def list_slugs(self) -> set[str]:
        """List all epic slugs."""
        return self._list_slugs()

    async def list_filtered(
        self,
        contains_story: str | None = None,
        has_stories: bool | None = None,
    ) -> list[Epic]:
        """List epics matching filters.

        Uses AND logic when multiple filters are provided.
        """
        epics = list(self.storage.values())

        # Filter by story reference
        if contains_story is not None:
            story_normalized = normalize_name(contains_story)
            epics = [
                e for e in epics
                if any(normalize_name(ref) == story_normalized for ref in e.story_refs)
            ]

        # Filter by has_stories
        if has_stories is not None:
            if has_stories:
                epics = [e for e in epics if e.story_refs]
            else:
                epics = [e for e in epics if not e.story_refs]

        return epics
