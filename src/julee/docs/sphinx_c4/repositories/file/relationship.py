"""File-backed Relationship repository implementation."""

import json
import logging
from pathlib import Path

from ...domain.models.relationship import ElementType, Relationship
from ...domain.repositories.relationship import RelationshipRepository
from .base import FileRepositoryMixin

logger = logging.getLogger(__name__)


class FileRelationshipRepository(
    FileRepositoryMixin[Relationship], RelationshipRepository
):
    """File-backed implementation of RelationshipRepository.

    Stores relationships as JSON files in the specified directory.
    File structure: {base_path}/{slug}.json
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize repository with base path.

        Args:
            base_path: Directory to store relationship JSON files
        """
        self.base_path = base_path
        self.storage: dict[str, Relationship] = {}
        self.entity_name = "Relationship"
        self.id_field = "slug"
        self._load_all()

    def _get_file_path(self, entity: Relationship) -> Path:
        """Get file path for a relationship."""
        return self.base_path / f"{entity.slug}.json"

    def _serialize(self, entity: Relationship) -> str:
        """Serialize relationship to JSON."""
        return entity.model_dump_json(indent=2)

    def _load_all(self) -> None:
        """Load all relationships from disk."""
        if not self.base_path.exists():
            logger.debug(f"FileRelationshipRepository: Base path does not exist: {self.base_path}")
            return

        for file_path in self.base_path.glob("*.json"):
            try:
                content = file_path.read_text(encoding="utf-8")
                data = json.loads(content)
                relationship = Relationship.model_validate(data)
                self.storage[relationship.slug] = relationship
                logger.debug(f"FileRelationshipRepository: Loaded {relationship.slug}")
            except Exception as e:
                logger.warning(f"FileRelationshipRepository: Failed to load {file_path}: {e}")

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
            if r.destination_type == element_type
            and r.destination_slug == element_slug
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
        to_remove = [
            slug for slug, r in self.storage.items() if r.docname == docname
        ]
        for slug in to_remove:
            await self.delete(slug)
        return len(to_remove)
