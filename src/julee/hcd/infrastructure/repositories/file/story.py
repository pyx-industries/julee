"""File-backed implementation of StoryRepository."""

import logging
from pathlib import Path

from julee.core.infrastructure.repositories.file.base import FileRepositoryMixin
from julee.hcd.entities.story import Story
from julee.hcd.parsers.gherkin import scan_feature_directory
from julee.hcd.repositories.story import StoryRepository
from julee.hcd.serializers.gherkin import get_story_filename, serialize_story
from julee.hcd.utils import normalize_name

logger = logging.getLogger(__name__)


class FileStoryRepository(FileRepositoryMixin[Story], StoryRepository):
    """File-backed implementation of StoryRepository.

    Stories are stored as Gherkin .feature files in the directory structure:
    {base_path}/{app_slug}/{feature_slug}.feature
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize with base path for feature files.

        Args:
            base_path: Root directory for feature files (e.g., docs/features/)
        """
        self.base_path = Path(base_path)
        self.storage: dict[str, Story] = {}
        self.entity_name = "Story"
        self.id_field = "slug"

        # Load existing stories from disk
        self._load_all()

    def _get_file_path(self, entity: Story) -> Path:
        """Get file path for a story."""
        filename = get_story_filename(entity)
        return self.base_path / entity.app_slug / filename

    def _serialize(self, entity: Story) -> str:
        """Serialize story to Gherkin format."""
        return serialize_story(entity)

    def _load_all(self) -> None:
        """Load all stories from feature files."""
        if not self.base_path.exists():
            logger.info(f"Feature directory not found: {self.base_path}")
            return

        stories = scan_feature_directory(self.base_path, self.base_path.parent)
        for story in stories:
            self.storage[story.slug] = story

        logger.info(f"Loaded {len(self.storage)} stories from {self.base_path}")

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
