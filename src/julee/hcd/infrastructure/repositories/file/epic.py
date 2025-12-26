"""File-backed implementation of EpicRepository."""

import logging
from pathlib import Path

from julee.core.infrastructure.repositories.file.base import FileRepositoryMixin
from julee.hcd.entities.epic import Epic
from julee.hcd.parsers.rst import scan_epic_directory
from julee.hcd.repositories.epic import EpicRepository
from julee.hcd.serializers.rst import serialize_epic
from julee.hcd.utils import normalize_name

logger = logging.getLogger(__name__)


class FileEpicRepository(FileRepositoryMixin[Epic], EpicRepository):
    """File-backed implementation of EpicRepository.

    Epics are stored as RST files with define-epic directives:
    {base_path}/{epic_slug}.rst
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize with base path for epic RST files.

        Args:
            base_path: Root directory for epic files (e.g., docs/epics/)
        """
        self.base_path = Path(base_path)
        self.storage: dict[str, Epic] = {}
        self.entity_name = "Epic"
        self.id_field = "slug"

        # Load existing epics from disk
        self._load_all()

    def _get_file_path(self, entity: Epic) -> Path:
        """Get file path for an epic."""
        return self.base_path / f"{entity.slug}.rst"

    def _serialize(self, entity: Epic) -> str:
        """Serialize epic to RST format."""
        return serialize_epic(entity)

    def _load_all(self) -> None:
        """Load all epics from RST files."""
        if not self.base_path.exists():
            logger.info(f"Epics directory not found: {self.base_path}")
            return

        epics = scan_epic_directory(self.base_path)
        for epic in epics:
            self.storage[epic.slug] = epic

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
