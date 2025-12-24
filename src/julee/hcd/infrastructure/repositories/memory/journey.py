"""Memory implementation of JourneyRepository."""

import logging

from julee.hcd.entities.journey import Journey
from julee.hcd.repositories.journey import JourneyRepository
from julee.hcd.utils import normalize_name

from .base import MemoryRepositoryMixin

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
