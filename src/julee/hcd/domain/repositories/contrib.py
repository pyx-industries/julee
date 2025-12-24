"""ContribRepository protocol.

Defines the interface for contrib module data access.
"""

from typing import Protocol, runtime_checkable

from julee.hcd.entities.contrib import ContribModule

from .base import BaseRepository


@runtime_checkable
class ContribRepository(BaseRepository[ContribModule], Protocol):
    """Repository protocol for ContribModule entities.

    Extends BaseRepository with contrib-specific query methods.
    Contrib modules are defined in RST documents and support incremental builds
    via docname tracking.
    """

    async def get_by_docname(self, docname: str) -> list[ContribModule]:
        """Get all contrib modules defined in a specific document.

        Args:
            docname: RST document name

        Returns:
            List of contrib modules from that document
        """
        ...

    async def clear_by_docname(self, docname: str) -> int:
        """Remove all contrib modules defined in a specific document.

        Used during incremental builds when a document is re-read.

        Args:
            docname: RST document name

        Returns:
            Number of contrib modules removed
        """
        ...
