"""SoftwareSystemRepository protocol."""

from typing import Protocol, runtime_checkable

from julee.c4.entities.software_system import SoftwareSystem, SystemType

from .base import BaseRepository


@runtime_checkable
class SoftwareSystemRepository(BaseRepository[SoftwareSystem], Protocol):
    """Repository protocol for SoftwareSystem entities.

    Extends BaseRepository with system-specific queries needed
    for C4 diagram generation.
    """

    async def get_by_type(self, system_type: SystemType) -> list[SoftwareSystem]:
        """Get all systems of a specific type.

        Args:
            system_type: internal, external, or existing

        Returns:
            List of systems matching the type
        """
        ...

    async def get_internal_systems(self) -> list[SoftwareSystem]:
        """Get all internal (owned) systems.

        Returns:
            List of internal systems for landscape diagrams
        """
        ...

    async def get_external_systems(self) -> list[SoftwareSystem]:
        """Get all external systems.

        Returns:
            List of external systems for context diagrams
        """
        ...

    async def get_by_tag(self, tag: str) -> list[SoftwareSystem]:
        """Get systems with a specific tag.

        Args:
            tag: Tag to filter by (case-insensitive)

        Returns:
            List of systems with the tag
        """
        ...

    async def get_by_owner(self, owner: str) -> list[SoftwareSystem]:
        """Get systems owned by a specific team.

        Args:
            owner: Team/organization name

        Returns:
            List of systems owned by that team
        """
        ...

    async def get_by_docname(self, docname: str) -> list[SoftwareSystem]:
        """Get systems defined in a specific document.

        Args:
            docname: Sphinx document name

        Returns:
            List of systems defined in that document
        """
        ...

    async def clear_by_docname(self, docname: str) -> int:
        """Clear systems defined in a specific document.

        Used for Sphinx incremental builds.

        Args:
            docname: Sphinx document name

        Returns:
            Number of systems removed
        """
        ...
