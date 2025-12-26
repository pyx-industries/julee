"""File-backed implementation of JourneyRepository."""

import logging
from pathlib import Path

from julee.core.infrastructure.repositories.file.base import FileRepositoryMixin
from julee.hcd.entities.journey import Journey, StepType
from julee.hcd.parsers.rst import scan_journey_directory
from julee.hcd.repositories.journey import JourneyRepository
from julee.hcd.serializers.rst import serialize_journey
from julee.hcd.utils import normalize_name

logger = logging.getLogger(__name__)


class FileJourneyRepository(FileRepositoryMixin[Journey], JourneyRepository):
    """File-backed implementation of JourneyRepository.

    Journeys are stored as RST files with define-journey directives:
    {base_path}/{journey_slug}.rst
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize with base path for journey RST files.

        Args:
            base_path: Root directory for journey files (e.g., docs/journeys/)
        """
        self.base_path = Path(base_path)
        self.storage: dict[str, Journey] = {}
        self.entity_name = "Journey"
        self.id_field = "slug"

        # Load existing journeys from disk
        self._load_all()

    def _get_file_path(self, entity: Journey) -> Path:
        """Get file path for a journey."""
        return self.base_path / f"{entity.slug}.rst"

    def _serialize(self, entity: Journey) -> str:
        """Serialize journey to RST format."""
        return serialize_journey(entity)

    def _load_all(self) -> None:
        """Load all journeys from RST files."""
        if not self.base_path.exists():
            logger.info(f"Journeys directory not found: {self.base_path}")
            return

        journeys = scan_journey_directory(self.base_path)
        for journey in journeys:
            self.storage[journey.slug] = journey

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
            if journey_slug in journey.depends_on
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
                step.step_type == StepType.STORY
                and normalize_name(step.ref) == story_normalized
                for step in journey.steps
            )
        ]

    async def get_with_epic_ref(self, epic_slug: str) -> list[Journey]:
        """Get journeys that reference a specific epic."""
        return [
            journey
            for journey in self.storage.values()
            if any(
                step.step_type == StepType.EPIC and step.ref == epic_slug
                for step in journey.steps
            )
        ]

    async def list_filtered(
        self,
        persona: str | None = None,
        contains_story: str | None = None,
    ) -> list[Journey]:
        """List journeys matching filters.

        Delegates to optimized get_by_* methods when possible.
        Uses AND logic when multiple filters are provided.
        """
        # No filters - return all
        if persona is None and contains_story is None:
            return await self.list_all()

        # Single filter - use optimized methods
        if persona and not contains_story:
            return await self.get_by_persona(persona)
        if contains_story and not persona:
            return await self.get_with_story_ref(contains_story)

        # Multiple filters - intersect results
        by_persona = {j.slug for j in await self.get_by_persona(persona)}
        by_story = await self.get_with_story_ref(contains_story)
        return [j for j in by_story if j.slug in by_persona]
