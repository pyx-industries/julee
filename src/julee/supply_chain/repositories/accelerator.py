"""AcceleratorRepository protocol.

Defines the interface for accelerator data access.
"""

from typing import Protocol, runtime_checkable

from julee.core.repositories.base import BaseRepository
from julee.supply_chain.entities.accelerator import Accelerator


@runtime_checkable
class AcceleratorRepository(BaseRepository[Accelerator], Protocol):
    """Repository protocol for Accelerator entities.

    Extends BaseRepository with accelerator-specific query methods.
    Accelerators are defined in RST documents and support incremental builds
    via docname tracking.
    """

    async def get_by_status(self, status: str) -> list[Accelerator]:
        """Get all accelerators with a specific status.

        Args:
            status: Status to filter by (case-insensitive)

        Returns:
            List of accelerators with matching status
        """
        ...

    async def get_by_docname(self, docname: str) -> list[Accelerator]:
        """Get all accelerators defined in a specific document.

        Args:
            docname: RST document name

        Returns:
            List of accelerators from that document
        """
        ...

    async def clear_by_docname(self, docname: str) -> int:
        """Remove all accelerators defined in a specific document.

        Used during incremental builds when a document is re-read.

        Args:
            docname: RST document name

        Returns:
            Number of accelerators removed
        """
        ...

    async def get_by_integration(
        self, integration_slug: str, relationship: str
    ) -> list[Accelerator]:
        """Get accelerators that have a relationship with an integration.

        Args:
            integration_slug: Integration slug to search for
            relationship: Either "sources_from" or "publishes_to"

        Returns:
            List of accelerators with this integration relationship
        """
        ...

    async def get_dependents(self, accelerator_slug: str) -> list[Accelerator]:
        """Get accelerators that depend on a specific accelerator.

        Args:
            accelerator_slug: Slug of the accelerator to find dependents of

        Returns:
            List of accelerators that have this accelerator in depends_on
        """
        ...

    async def get_fed_by(self, accelerator_slug: str) -> list[Accelerator]:
        """Get accelerators that feed into a specific accelerator.

        Args:
            accelerator_slug: Slug of the accelerator

        Returns:
            List of accelerators that have this accelerator in feeds_into
        """
        ...

    async def get_all_statuses(self) -> set[str]:
        """Get all unique statuses across all accelerators.

        Returns:
            Set of status strings (normalized to lowercase)
        """
        ...

    async def list_filtered(
        self,
        solution_slug: str | None = None,
        status: str | None = None,
    ) -> list[Accelerator]:
        """List accelerators matching filters.

        Filter parameters declared here are automatically surfaced as
        FastAPI query params via make_list_request(). Implementations
        should use AND logic when multiple filters are provided.

        Args:
            solution_slug: Filter to accelerators for this solution
            status: Filter to accelerators with this status

        Returns:
            List of accelerators matching all provided filters
        """
        ...
