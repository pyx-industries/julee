"""SphinxEnv implementation of RelationshipRepository."""

from julee.c4.entities.relationship import ElementType, Relationship
from julee.c4.repositories.relationship import RelationshipRepository

from .base import SphinxEnvC4RepositoryMixin


class SphinxEnvRelationshipRepository(
    SphinxEnvC4RepositoryMixin[Relationship], RelationshipRepository
):
    """SphinxEnv implementation of RelationshipRepository."""

    entity_class = Relationship

    async def get_for_element(
        self, element_type: ElementType, element_slug: str
    ) -> list[Relationship]:
        """Get all relationships involving an element."""
        all_rels = await self.list_all()
        return [
            r for r in all_rels
            if (r.source_type == element_type and r.source_slug == element_slug)
            or (r.destination_type == element_type and r.destination_slug == element_slug)
        ]

    async def get_outgoing(
        self, element_type: ElementType, element_slug: str
    ) -> list[Relationship]:
        """Get relationships where element is the source."""
        all_rels = await self.list_all()
        return [
            r for r in all_rels
            if r.source_type == element_type and r.source_slug == element_slug
        ]

    async def get_incoming(
        self, element_type: ElementType, element_slug: str
    ) -> list[Relationship]:
        """Get relationships where element is the destination."""
        all_rels = await self.list_all()
        return [
            r for r in all_rels
            if r.destination_type == element_type and r.destination_slug == element_slug
        ]

    async def get_person_relationships(self) -> list[Relationship]:
        """Get all relationships involving persons."""
        all_rels = await self.list_all()
        return [
            r for r in all_rels
            if r.source_type == ElementType.PERSON or r.destination_type == ElementType.PERSON
        ]

    async def get_cross_system_relationships(self) -> list[Relationship]:
        """Get relationships between different systems."""
        all_rels = await self.list_all()
        return [
            r for r in all_rels
            if r.source_type == ElementType.SOFTWARE_SYSTEM
            and r.destination_type == ElementType.SOFTWARE_SYSTEM
        ]

    async def get_between_containers(self, system_slug: str) -> list[Relationship]:
        """Get relationships between containers within a system."""
        all_rels = await self.list_all()
        return [
            r for r in all_rels
            if r.source_type == ElementType.CONTAINER
            and r.destination_type == ElementType.CONTAINER
        ]

    async def get_between_components(self, container_slug: str) -> list[Relationship]:
        """Get relationships between components within a container."""
        all_rels = await self.list_all()
        return [
            r for r in all_rels
            if r.source_type == ElementType.COMPONENT
            and r.destination_type == ElementType.COMPONENT
        ]
