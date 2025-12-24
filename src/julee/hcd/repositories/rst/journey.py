"""RST file-backed implementation of JourneyRepository."""

import logging
from pathlib import Path

from julee.hcd.entities.journey import Journey, JourneyStep
from julee.hcd.utils import normalize_name

from ...domain.repositories.journey import JourneyRepository
from ...parsers.docutils_parser import (
    ParsedDocument,
    extract_nested_directives,
    parse_comma_list,
    parse_multiline_list,
)
from .base import RstRepositoryMixin

logger = logging.getLogger(__name__)


class RstJourneyRepository(RstRepositoryMixin[Journey], JourneyRepository):
    """RST file-backed implementation of JourneyRepository.

    Journeys are stored as individual RST files in a directory.
    Each file contains a single define-journey directive.
    """

    entity_name = "Journey"
    id_field = "slug"
    entity_type = "journey"
    directive_name = "define-journey"

    def __init__(self, base_dir: Path) -> None:
        """Initialize with base directory.

        Args:
            base_dir: Directory containing journey RST files
        """
        super().__init__(base_dir)

    def _build_entity(
        self,
        data: dict,
        parsed: ParsedDocument,
        docname: str,
    ) -> Journey:
        """Build Journey entity from parsed data.

        Args:
            data: Entity data from parsed directive
            parsed: Full ParsedDocument for structure extraction
            docname: Document name (file stem)

        Returns:
            Journey entity
        """
        options = data.get("options", {})
        content = data.get("content", "")

        # Extract steps from the content
        nested = extract_nested_directives(content)
        steps = []
        for item in nested:
            if item.directive_type == "step-story":
                steps.append(JourneyStep.story(item.ref))
            elif item.directive_type == "step-epic":
                steps.append(JourneyStep.epic(item.ref))
            elif item.directive_type == "step-phase":
                steps.append(JourneyStep.phase(item.ref, item.description))

        # Extract goal (content before any step directives)
        goal = self._extract_goal(content)

        return Journey(
            slug=data["slug"],
            persona=options.get("persona", ""),
            intent=options.get("intent", ""),
            outcome=options.get("outcome", ""),
            goal=goal,
            depends_on=parse_comma_list(options.get("depends-on", "")),
            preconditions=parse_multiline_list(options.get("preconditions", "")),
            postconditions=parse_multiline_list(options.get("postconditions", "")),
            steps=steps,
            docname=docname,
            page_title=parsed.title,
            preamble_rst=parsed.preamble,
            epilogue_rst=parsed.epilogue,
        )

    def _extract_goal(self, content: str) -> str:
        """Extract goal text (content before step directives).

        Args:
            content: Directive content

        Returns:
            Goal text
        """
        lines = []
        for line in content.split("\n"):
            stripped = line.strip()
            # Stop at first step directive
            if stripped.startswith(".. step-"):
                break
            lines.append(line)

        # Strip trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()

        return "\n".join(lines).strip()

    # Query methods from JourneyRepository protocol

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
