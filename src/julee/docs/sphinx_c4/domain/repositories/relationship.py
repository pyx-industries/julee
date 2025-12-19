"""RelationshipRepository protocol."""

from typing import Protocol, runtime_checkable

from ..models.relationship import ElementType, Relationship
from .base import BaseRepository


@runtime_checkable
class RelationshipRepository(BaseRepository[Relationship], Protocol):
    """Repository protocol for Relationship entities.

    Critical for diagram generation - provides queries to find
    all relationships involving specific elements or types.
    """

    async def get_for_element(
        self,
        element_type: ElementType,
        element_slug: str,
    ) -> list[Relationship]:
        """Get all relationships involving an element (as source or destination).

        Args:
            element_type: Type of element
            element_slug: Element's slug

        Returns:
            List of relationships involving the element
        """
        ...

    async def get_outgoing(
        self,
        element_type: ElementType,
        element_slug: str,
    ) -> list[Relationship]:
        """Get relationships where element is the source.

        Args:
            element_type: Type of source element
            element_slug: Source element's slug

        Returns:
            List of outgoing relationships
        """
        ...

    async def get_incoming(
        self,
        element_type: ElementType,
        element_slug: str,
    ) -> list[Relationship]:
        """Get relationships where element is the destination.

        Args:
            element_type: Type of destination element
            element_slug: Destination element's slug

        Returns:
            List of incoming relationships
        """
        ...

    async def get_person_relationships(self) -> list[Relationship]:
        """Get all relationships involving persons (for context diagrams).

        Returns:
            List of relationships with person as source or destination
        """
        ...

    async def get_cross_system_relationships(self) -> list[Relationship]:
        """Get relationships between different systems.

        Returns:
            List of system-to-system relationships for landscape diagrams
        """
        ...

    async def get_between_containers(self, system_slug: str) -> list[Relationship]:
        """Get relationships between containers within a system.

        Args:
            system_slug: System to filter relationships for

        Returns:
            List of container-to-container relationships
        """
        ...

    async def get_between_components(self, container_slug: str) -> list[Relationship]:
        """Get relationships between components within a container.

        Args:
            container_slug: Container to filter relationships for

        Returns:
            List of component-to-component relationships
        """
        ...

    async def get_by_docname(self, docname: str) -> list[Relationship]:
        """Get relationships defined in a specific document.

        Args:
            docname: Sphinx document name

        Returns:
            List of relationships defined in that document
        """
        ...

    async def clear_by_docname(self, docname: str) -> int:
        """Clear relationships defined in a specific document.

        Args:
            docname: Sphinx document name

        Returns:
            Number of relationships removed
        """
        ...
