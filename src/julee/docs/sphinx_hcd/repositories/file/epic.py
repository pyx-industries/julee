"""File-backed implementation of EpicRepository."""

import logging
from pathlib import Path

from ...domain.models.epic import Epic
from ...domain.repositories.epic import EpicRepository
from ...serializers.rst import serialize_epic
from ...utils import normalize_name
from .base import FileRepositoryMixin

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
        """Load all epics from RST files.

        Note: This is a simplified implementation that doesn't parse
        existing RST files. Full RST parsing would require Sphinx.
        For now, only tracks epics created through this repository.
        """
        if not self.base_path.exists():
            logger.info(f"Epics directory not found: {self.base_path}")
            return

        # Count existing RST files for info
        rst_files = list(self.base_path.glob("*.rst"))
        if rst_files:
            logger.info(
                f"Found {len(rst_files)} epic RST files in {self.base_path}. "
                "Full parsing not implemented - start with empty storage."
            )

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
