"""ContribRepository protocol.

Defines the interface for contrib module data access.
"""

from typing import Protocol, runtime_checkable

from julee.core.repositories.base import BaseRepository
from julee.hcd.entities.contrib import ContribModule


@runtime_checkable
class ContribRepository(BaseRepository[ContribModule], Protocol):
    """Repository protocol for ContribModule entities.

    Extends BaseRepository with contrib-specific query methods.
    Contrib modules are defined in RST documents and support incremental builds
    via docname tracking.
    """

    async def list_filtered(
        self, solution_slug: str | None = None
    ) -> list[ContribModule]:
        """List contrib modules with optional solution filter.

        Args:
            solution_slug: Filter by solution (None = all solutions)

        Returns:
            List of matching contrib modules
        """
        ...

    async def list_slugs(self, solution_slug: str | None = None) -> list[str]:
        """List all contrib module slugs with optional solution filter.

        Args:
            solution_slug: Filter by solution (None = all solutions)

        Returns:
            List of matching slugs
        """
        ...

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
