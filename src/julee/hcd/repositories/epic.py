"""EpicRepository protocol.

Defines the interface for epic data access.
"""

from typing import Protocol, runtime_checkable

from julee.hcd.entities.epic import Epic

from .base import BaseRepository


@runtime_checkable
class EpicRepository(BaseRepository[Epic], Protocol):
    """Repository protocol for Epic entities.

    Extends BaseRepository with epic-specific query methods.
    Epics are defined in RST documents and support incremental builds
    via docname tracking.
    """

    async def get_by_docname(self, docname: str) -> list[Epic]:
        """Get all epics defined in a specific document.

        Args:
            docname: RST document name

        Returns:
            List of epics from that document
        """
        ...

    async def clear_by_docname(self, docname: str) -> int:
        """Remove all epics defined in a specific document.

        Used during incremental builds when a document is re-read.

        Args:
            docname: RST document name

        Returns:
            Number of epics removed
        """
        ...

    async def get_with_story_ref(self, story_title: str) -> list[Epic]:
        """Get epics that contain a specific story.

        Args:
            story_title: Story feature title (case-insensitive)

        Returns:
            List of epics containing this story in story_refs
        """
        ...

    async def get_all_story_refs(self) -> set[str]:
        """Get all unique story references across all epics.

        Returns:
            Set of story titles (normalized)
        """
        ...
