"""RST file-backed implementation of EpicRepository."""

import logging
from pathlib import Path

from ...domain.models.epic import Epic
from ...domain.repositories.epic import EpicRepository
from ...parsers.docutils_parser import ParsedDocument, extract_story_refs
from julee.hcd.utils import normalize_name
from .base import RstRepositoryMixin

logger = logging.getLogger(__name__)


class RstEpicRepository(RstRepositoryMixin[Epic], EpicRepository):
    """RST file-backed implementation of EpicRepository.

    Epics are stored as individual RST files in a directory.
    Each file contains a single define-epic directive with
    epic-story child directives.
    """

    entity_name = "Epic"
    id_field = "slug"
    entity_type = "epic"
    directive_name = "define-epic"

    def __init__(self, base_dir: Path) -> None:
        """Initialize with base directory.

        Args:
            base_dir: Directory containing epic RST files
        """
        super().__init__(base_dir)

    def _build_entity(
        self,
        data: dict,
        parsed: ParsedDocument,
        docname: str,
    ) -> Epic:
        """Build Epic entity from parsed data.

        Args:
            data: Entity data from parsed directive
            parsed: Full ParsedDocument for structure extraction
            docname: Document name (file stem)

        Returns:
            Epic entity
        """
        content = data.get("content", "")

        # Extract story references from epic-story directives
        story_refs = extract_story_refs(content)

        # Extract description (content before epic-story directives)
        description = self._extract_description(content)

        return Epic(
            slug=data["slug"],
            description=description,
            story_refs=story_refs,
            docname=docname,
            page_title=parsed.title,
            preamble_rst=parsed.preamble,
            epilogue_rst=parsed.epilogue,
        )

    def _extract_description(self, content: str) -> str:
        """Extract description (content before epic-story directives).

        Args:
            content: Directive content

        Returns:
            Description text
        """
        lines = []
        for line in content.split("\n"):
            stripped = line.strip()
            # Stop at first epic-story directive
            if stripped.startswith(".. epic-story::"):
                break
            lines.append(line)

        # Strip trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()

        return "\n".join(lines).strip()

    # Query methods from EpicRepository protocol

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
        refs = set()
        for epic in self.storage.values():
            refs.update(normalize_name(ref) for ref in epic.story_refs)
        return refs
