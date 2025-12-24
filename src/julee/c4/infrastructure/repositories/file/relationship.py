"""File-backed Relationship repository implementation."""

import logging
from pathlib import Path

from julee.c4.entities.relationship import ElementType, Relationship
from julee.c4.parsers.rst import scan_relationship_directory
from julee.c4.repositories.relationship import RelationshipRepository
from julee.c4.serializers.rst import serialize_relationship
from julee.core.infrastructure.repositories.file.base import FileRepositoryMixin

logger = logging.getLogger(__name__)


class FileRelationshipRepository(
    FileRepositoryMixin[Relationship], RelationshipRepository
):
    """File-backed implementation of RelationshipRepository.

    Stores relationships as RST files with define-relationship directives.
    File structure: {base_path}/{slug}.rst
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize repository with base path.

        Args:
            base_path: Directory to store relationship RST files
        """
        self.base_path = base_path
        self.storage: dict[str, Relationship] = {}
        self.entity_name = "Relationship"
        self.id_field = "slug"
        self._load_all()

    def _get_file_path(self, entity: Relationship) -> Path:
        """Get file path for a relationship."""
        return self.base_path / f"{entity.slug}.rst"

    def _serialize(self, entity: Relationship) -> str:
        """Serialize relationship to RST format."""
        return serialize_relationship(entity)

    def _load_all(self) -> None:
        """Load all relationships from disk."""
        if not self.base_path.exists():
            logger.debug(
                f"FileRelationshipRepository: Base path does not exist: {self.base_path}"
            )
            return

        relationships = scan_relationship_directory(self.base_path)
        for relationship in relationships:
            self.storage[relationship.slug] = relationship

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
        """Get relationships between containers within a system."""
        return [
            r
            for r in self.storage.values()
            if r.source_type == ElementType.CONTAINER
            and r.destination_type == ElementType.CONTAINER
        ]

    async def get_between_components(self, container_slug: str) -> list[Relationship]:
        """Get relationships between components within a container."""
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
            await self.delete(slug)
        return len(to_remove)
