"""RST file-backed implementation of StoryRepository."""

import logging
from pathlib import Path

from julee.hcd.entities.story import Story
from julee.hcd.parsers.docutils_parser import ParsedDocument
from julee.hcd.repositories.story import StoryRepository
from julee.hcd.utils import normalize_name

from .base import RstRepositoryMixin

logger = logging.getLogger(__name__)


class RstStoryRepository(RstRepositoryMixin[Story], StoryRepository):
    """RST file-backed implementation of StoryRepository.

    Stories are stored as individual RST files in a directory.
    Each file contains a single define-story directive with
    Gherkin-format content.
    """

    entity_name = "Story"
    id_field = "slug"
    entity_type = "story"
    directive_name = "define-story"

    def __init__(self, base_dir: Path) -> None:
        """Initialize with base directory.

        Args:
            base_dir: Directory containing story RST files
        """
        super().__init__(base_dir)

    def _build_entity(
        self,
        data: dict,
        parsed: ParsedDocument,
        docname: str,
    ) -> Story:
        """Build Story entity from parsed data."""
        options = data.get("options", {})
        content = data.get("content", "")

        # Parse Gherkin content
        feature_title, persona, i_want, so_that, gherkin_snippet = (
            self._parse_gherkin_content(content)
        )

        return Story(
            slug=data["slug"],
            feature_title=feature_title or data["slug"].replace("-", " ").title(),
            persona=options.get("persona", persona or "unknown"),
            i_want=i_want or "do something",
            so_that=so_that or "",
            app_slug=options.get("app", "unknown"),
            file_path=f"{docname}.rst",
            gherkin_snippet=gherkin_snippet,
            page_title=parsed.title,
            preamble_rst=parsed.preamble,
            epilogue_rst=parsed.epilogue,
        )

    def _parse_gherkin_content(self, content: str) -> tuple[str, str, str, str, str]:
        """Parse Gherkin-format content from directive body.

        Args:
            content: Directive content

        Returns:
            Tuple of (feature_title, persona, i_want, so_that, gherkin_snippet)
        """
        feature_title = ""
        persona = ""
        i_want = ""
        so_that = ""
        gherkin_lines = []

        lines = content.split("\n")
        for line in lines:
            stripped = line.strip()

            if stripped.startswith("Feature:"):
                feature_title = stripped[8:].strip()
            elif stripped.startswith("As a "):
                persona = stripped[5:].strip()
            elif stripped.startswith("I want to "):
                i_want = stripped[10:].strip()
            elif stripped.startswith("I want "):
                i_want = stripped[7:].strip()
            elif stripped.startswith("So that "):
                so_that = stripped[8:].strip()

            # Collect all content as gherkin snippet
            gherkin_lines.append(line)

        return (
            feature_title,
            persona,
            i_want,
            so_that,
            "\n".join(gherkin_lines).strip(),
        )

    # Query methods from StoryRepository protocol

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

    async def get_by_feature_title(self, feature_title: str) -> Story | None:
        """Get a story by its feature title."""
        title_normalized = normalize_name(feature_title)
        for story in self.storage.values():
            if normalize_name(story.feature_title) == title_normalized:
                return story
        return None

    async def get_apps_with_stories(self) -> set[str]:
        """Get the set of app slugs that have stories."""
        return {
            story.app_normalized
            for story in self.storage.values()
            if story.app_normalized
        }

    async def get_all_personas(self) -> set[str]:
        """Get all unique personas across all stories."""
        return {
            story.persona_normalized
            for story in self.storage.values()
            if story.persona_normalized
        }
