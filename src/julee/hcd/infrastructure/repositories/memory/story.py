"""Memory implementation of StoryRepository."""

import logging

from julee.core.infrastructure.repositories.memory.base import MemoryRepositoryMixin
from julee.hcd.entities.story import Story
from julee.hcd.repositories.story import StoryRepository
from julee.hcd.utils import normalize_name

logger = logging.getLogger(__name__)


class MemoryStoryRepository(MemoryRepositoryMixin[Story], StoryRepository):
    """In-memory implementation of StoryRepository.

    Stories are stored in a dictionary keyed by slug. This implementation
    is used during Sphinx builds where stories are populated at builder-inited
    and queried during doctree processing.
    """

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.storage: dict[str, Story] = {}
        self.entity_name = "Story"
        self.id_field = "slug"

    # -------------------------------------------------------------------------
    # BaseRepository implementation (delegating to protected helpers)
    # -------------------------------------------------------------------------

    async def get(self, entity_id: str) -> Story | None:
        """Get a story by slug."""
        return self._get_entity(entity_id)

    async def get_many(self, entity_ids: list[str]) -> dict[str, Story | None]:
        """Get multiple stories by slug."""
        return self._get_many_entities(entity_ids)

    async def save(self, entity: Story) -> None:
        """Save a story."""
        self._save_entity(entity)

    async def list_all(self) -> list[Story]:
        """List all stories."""
        return self._list_all_entities()

    async def delete(self, entity_id: str) -> bool:
        """Delete a story by slug."""
        return self._delete_entity(entity_id)

    async def clear(self) -> None:
        """Clear all stories."""
        self._clear_storage()

    # -------------------------------------------------------------------------
    # StoryRepository-specific queries
    # -------------------------------------------------------------------------

    async def get_by_app(self, app_slug: str) -> list[Story]:
        """Get all stories for an application."""
        app_normalized = normalize_name(app_slug)
        return [
            story
            for story in self.storage.values()
            if story.app_normalized == app_normalized
        ]

    async def get_by_persona(self, persona: str) -> list[Story]:
        """Get all stories for a persona."""
        persona_normalized = normalize_name(persona)
        return [
            story
            for story in self.storage.values()
            if story.persona_normalized == persona_normalized
        ]

    async def list_filtered(
        self,
        app_slug: str | None = None,
        persona: str | None = None,
    ) -> list[Story]:
        """List stories matching filters.

        Delegates to optimized get_by_* methods when possible.
        Uses AND logic when multiple filters are provided.
        """
        # No filters - return all
        if app_slug is None and persona is None:
            return await self.list_all()

        # Single filter - use optimized methods
        if app_slug and not persona:
            return await self.get_by_app(app_slug)
        if persona and not app_slug:
            return await self.get_by_persona(persona)

        # Multiple filters - intersect results
        by_app = {s.slug for s in await self.get_by_app(app_slug)}
        by_persona = await self.get_by_persona(persona)
        return [s for s in by_persona if s.slug in by_app]

    async def get_by_feature_title(self, feature_title: str) -> Story | None:
        """Get a story by its feature title."""
        title_normalized = normalize_name(feature_title)
        for story in self.storage.values():
            if normalize_name(story.feature_title) == title_normalized:
                return story
        return None

    async def get_apps_with_stories(self) -> set[str]:
        """Get the set of app slugs that have stories."""
        return {story.app_slug for story in self.storage.values()}

    async def get_all_personas(self) -> set[str]:
        """Get all unique personas across all stories."""
        return {
            story.persona_normalized
            for story in self.storage.values()
            if story.persona_normalized != "unknown"
        }

    async def list_slugs(self) -> set[str]:
        """List all story slugs."""
        return self._list_slugs()

    async def get_title_map(self) -> dict[str, Story]:
        """Get mapping of normalized feature titles to stories."""
        return {
            normalize_name(story.feature_title): story
            for story in self.storage.values()
        }
