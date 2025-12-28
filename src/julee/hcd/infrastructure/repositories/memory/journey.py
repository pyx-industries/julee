"""Memory implementation of JourneyRepository."""

import logging

from julee.core.infrastructure.repositories.memory.base import MemoryRepositoryMixin
from julee.hcd.entities.journey import Journey
from julee.hcd.repositories.journey import JourneyRepository
from julee.hcd.utils import normalize_name

logger = logging.getLogger(__name__)


class MemoryJourneyRepository(MemoryRepositoryMixin[Journey], JourneyRepository):
    """In-memory implementation of JourneyRepository.

    Journeys are stored in a dictionary keyed by slug. This implementation
    is used during Sphinx builds where journeys are populated during doctree
    processing and support incremental builds via docname tracking.
    """

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.storage: dict[str, Journey] = {}
        self.entity_name = "Journey"
        self.id_field = "slug"

    # -------------------------------------------------------------------------
    # BaseRepository implementation (delegating to protected helpers)
    # -------------------------------------------------------------------------

    async def get(self, entity_id: str) -> Journey | None:
        """Get a journey by slug."""
        return self._get_entity(entity_id)

    async def get_many(self, entity_ids: list[str]) -> dict[str, Journey | None]:
        """Get multiple journeys by slug."""
        return self._get_many_entities(entity_ids)

    async def save(self, entity: Journey) -> None:
        """Save a journey."""
        self._save_entity(entity)

    async def list_all(self) -> list[Journey]:
        """List all journeys."""
        return self._list_all_entities()

    async def delete(self, entity_id: str) -> bool:
        """Delete a journey by slug."""
        return self._delete_entity(entity_id)

    async def clear(self) -> None:
        """Clear all journeys."""
        self._clear_storage()

    # -------------------------------------------------------------------------
    # JourneyRepository-specific queries
    # -------------------------------------------------------------------------

    async def get_by_persona(self, persona: str) -> list[Journey]:
        """Get all journeys for a persona."""
        persona_normalized = normalize_name(persona)
        return [
            journey
            for journey in self.storage.values()
            if journey.persona_normalized == persona_normalized
        ]

    async def get_by_docname(self, docname: str) -> list[Journey]:
        """Get all journeys defined in a specific document."""
        return [
            journey for journey in self.storage.values() if journey.docname == docname
        ]

    async def clear_by_docname(self, docname: str) -> int:
        """Remove all journeys defined in a specific document."""
        to_remove = [
            slug for slug, journey in self.storage.items() if journey.docname == docname
        ]
        for slug in to_remove:
            del self.storage[slug]
        return len(to_remove)

    async def get_dependents(self, journey_slug: str) -> list[Journey]:
        """Get journeys that depend on a specific journey."""
        return [
            journey
            for journey in self.storage.values()
            if journey.has_dependency(journey_slug)
        ]

    async def get_dependencies(self, journey_slug: str) -> list[Journey]:
        """Get journeys that a specific journey depends on."""
        journey = self.storage.get(journey_slug)
        if not journey:
            return []
        return [
            self.storage[dep_slug]
            for dep_slug in journey.depends_on
            if dep_slug in self.storage
        ]

    async def get_all_personas(self) -> set[str]:
        """Get all unique personas across all journeys."""
        return {
            journey.persona_normalized
            for journey in self.storage.values()
            if journey.persona_normalized
        }

    async def get_with_story_ref(self, story_title: str) -> list[Journey]:
        """Get journeys that reference a specific story."""
        story_normalized = normalize_name(story_title)
        return [
            journey
            for journey in self.storage.values()
            if any(
                normalize_name(ref) == story_normalized
                for ref in journey.get_story_refs()
            )
        ]

    async def get_with_epic_ref(self, epic_slug: str) -> list[Journey]:
        """Get journeys that reference a specific epic."""
        return [
            journey
            for journey in self.storage.values()
            if epic_slug in journey.get_epic_refs()
        ]

    async def list_slugs(self) -> set[str]:
        """List all journey slugs."""
        return self._list_slugs()

    async def list_filtered(
        self,
        solution_slug: str | None = None,
        persona: str | None = None,
        contains_story: str | None = None,
    ) -> list[Journey]:
        """List journeys matching filters.

        Uses AND logic when multiple filters are provided.
        """
        results = list(self.storage.values())

        # Filter by solution
        if solution_slug is not None:
            results = [j for j in results if j.solution_slug == solution_slug]

        # Filter by persona
        if persona is not None:
            persona_normalized = normalize_name(persona)
            results = [j for j in results if j.persona_normalized == persona_normalized]

        # Filter by story reference
        if contains_story is not None:
            story_normalized = normalize_name(contains_story)
            results = [
                j for j in results
                if any(normalize_name(ref) == story_normalized for ref in j.get_story_refs())
            ]

        return results
