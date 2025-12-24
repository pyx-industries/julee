"""In-memory Relationship repository implementation."""

from julee.c4.entities.relationship import ElementType, Relationship
from julee.c4.repositories.relationship import RelationshipRepository
from julee.shared.repositories.memory.base import MemoryRepositoryMixin


class MemoryRelationshipRepository(
    MemoryRepositoryMixin[Relationship], RelationshipRepository
):
    """In-memory implementation of RelationshipRepository.

    Stores relationships in a dictionary keyed by slug.
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        self.storage: dict[str, Relationship] = {}
        self.entity_name = "Relationship"
        self.id_field = "slug"

    async def get_for_element(
        self,
        element_type: ElementType,
        element_slug: str,
    ) -> list[Relationship]:
        """Get all relationships involving an element."""
        return [
            r
            for r in self.storage.values()
            if r.involves_element(element_type, element_slug)
        ]

    async def get_outgoing(
        self,
        element_type: ElementType,
        element_slug: str,
    ) -> list[Relationship]:
        """Get relationships where element is the source."""
        return [
            r
            for r in self.storage.values()
            if r.source_type == element_type and r.source_slug == element_slug
        ]

    async def get_incoming(
        self,
        element_type: ElementType,
        element_slug: str,
    ) -> list[Relationship]:
        """Get relationships where element is the destination."""
        return [
            r
            for r in self.storage.values()
            if r.destination_type == element_type and r.destination_slug == element_slug
        ]

    async def get_person_relationships(self) -> list[Relationship]:
        """Get all relationships involving persons."""
        return [r for r in self.storage.values() if r.is_person_relationship]

    async def get_cross_system_relationships(self) -> list[Relationship]:
        """Get relationships between different systems."""
        return [r for r in self.storage.values() if r.is_cross_system]

    async def get_between_containers(self, system_slug: str) -> list[Relationship]:
        """Get relationships between containers within a system.

        Note: This requires knowing which containers belong to the system.
        For simplicity, we filter relationships where both source and destination
        are containers. The caller should ensure containers are from the same system.
        """
        return [
            r
            for r in self.storage.values()
            if r.source_type == ElementType.CONTAINER
            and r.destination_type == ElementType.CONTAINER
        ]

    async def get_between_components(self, container_slug: str) -> list[Relationship]:
        """Get relationships between components within a container.

        Note: Similar to get_between_containers, we return component-to-component
        relationships. The caller should filter by container context.
        """
        return [
            r
            for r in self.storage.values()
            if r.source_type == ElementType.COMPONENT
            and r.destination_type == ElementType.COMPONENT
        ]

    async def get_by_docname(self, docname: str) -> list[Relationship]:
        """Get relationships defined in a specific document."""
        return [r for r in self.storage.values() if r.docname == docname]

    async def clear_by_docname(self, docname: str) -> int:
        """Clear relationships defined in a specific document."""
        to_remove = [slug for slug, r in self.storage.items() if r.docname == docname]
        for slug in to_remove:
            del self.storage[slug]
        return len(to_remove)
