"""Sphinx environment repository mixin.

Provides common functionality for repositories that store data in
Sphinx's BuildEnvironment for parallel-safe builds.
"""

import logging
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class SphinxEnvRepositoryMixin(Generic[T]):
    """Mixin for repositories storing data in Sphinx env.

    Stores entities as serialized dicts in env.hcd_storage[entity_key].
    This enables parallel builds since env is properly pickled between
    worker processes and merged back via env-merge-info event.

    Subclasses must provide:
    - self.env: BuildEnvironment reference
    - self.entity_name: str (e.g., "Accelerator") for logging
    - self.entity_key: str (e.g., "accelerators") storage key
    - self.id_field: str (e.g., "slug") entity ID field name
    - self.entity_class: type[T] the Pydantic model class

    Example:
        class SphinxEnvAcceleratorRepository(
            SphinxEnvRepositoryMixin[Accelerator], AcceleratorRepository
        ):
            def __init__(self, env: BuildEnvironment) -> None:
                self.env = env
                self.entity_name = "Accelerator"
                self.entity_key = "accelerators"
                self.id_field = "slug"
                self.entity_class = Accelerator
    """

    env: "BuildEnvironment"
    entity_name: str
    entity_key: str
    id_field: str
    entity_class: type[T]

    def _get_storage(self) -> dict[str, dict[str, Any]]:
        """Get or create storage dict for this entity type.

        Storage is located at env.hcd_storage[entity_key].
        Creates the nested structure if it doesn't exist.

        Returns:
            Dictionary mapping entity ID to serialized entity data
        """
        if not hasattr(self.env, "hcd_storage"):
            self.env.hcd_storage = {}
        if self.entity_key not in self.env.hcd_storage:
            self.env.hcd_storage[self.entity_key] = {}
        return self.env.hcd_storage[self.entity_key]

    def _get_entity_id(self, entity: T) -> str:
        """Extract entity ID from entity instance."""
        return getattr(entity, self.id_field)

    def _serialize(self, entity: T) -> dict[str, Any]:
        """Serialize entity to picklable dict.

        Uses Pydantic's model_dump() which handles nested models,
        enums, and other complex types correctly.
        """
        return entity.model_dump()

    def _deserialize(self, data: dict[str, Any]) -> T:
        """Reconstruct entity from serialized dict.

        Uses Pydantic model validation to reconstruct the entity.
        """
        return self.entity_class(**data)

    async def get(self, entity_id: str) -> T | None:
        """Retrieve entity by ID.

        Args:
            entity_id: Unique entity identifier

        Returns:
            Entity if found, None otherwise
        """
        storage = self._get_storage()
        data = storage.get(entity_id)
        if data is None:
            logger.debug(
                f"SphinxEnv{self.entity_name}Repository: {self.entity_name} not found",
                extra={f"{self.entity_name.lower()}_id": entity_id},
            )
            return None
        return self._deserialize(data)

    async def get_many(self, entity_ids: list[str]) -> dict[str, T | None]:
        """Retrieve multiple entities by ID.

        Args:
            entity_ids: List of unique entity identifiers

        Returns:
            Dict mapping entity_id to entity (or None if not found)
        """
        storage = self._get_storage()
        result: dict[str, T | None] = {}
        for entity_id in entity_ids:
            data = storage.get(entity_id)
            result[entity_id] = self._deserialize(data) if data else None
        return result

    async def save(self, entity: T) -> None:
        """Save entity to storage.

        Args:
            entity: Complete entity to save
        """
        entity_id = self._get_entity_id(entity)
        storage = self._get_storage()
        storage[entity_id] = self._serialize(entity)
        logger.debug(
            f"SphinxEnv{self.entity_name}Repository: Saved {self.entity_name}",
            extra={f"{self.entity_name.lower()}_id": entity_id},
        )

    async def list_all(self) -> list[T]:
        """List all entities.

        Returns:
            List of all entities in the repository
        """
        storage = self._get_storage()
        return [self._deserialize(data) for data in storage.values()]

    async def delete(self, entity_id: str) -> bool:
        """Delete entity by ID.

        Args:
            entity_id: Unique entity identifier

        Returns:
            True if entity was deleted, False if not found
        """
        storage = self._get_storage()
        if entity_id in storage:
            del storage[entity_id]
            logger.debug(
                f"SphinxEnv{self.entity_name}Repository: Deleted {self.entity_name}",
                extra={f"{self.entity_name.lower()}_id": entity_id},
            )
            return True
        return False

    async def clear(self) -> None:
        """Remove all entities from storage."""
        storage = self._get_storage()
        count = len(storage)
        storage.clear()
        logger.debug(
            f"SphinxEnv{self.entity_name}Repository: Cleared {count} entities",
        )

    # Common query methods used by multiple entity repositories

    async def find_by_field(self, field: str, value: Any) -> list[T]:
        """Find all entities where field equals value.

        Args:
            field: Field name to match
            value: Value to match

        Returns:
            List of matching entities
        """
        storage = self._get_storage()
        return [
            self._deserialize(data)
            for data in storage.values()
            if data.get(field) == value
        ]

    async def find_by_docname(self, docname: str) -> list[T]:
        """Find all entities defined in a specific document.

        Args:
            docname: RST document name

        Returns:
            List of entities defined in that document
        """
        return await self.find_by_field("docname", docname)

    async def clear_by_docname(self, docname: str) -> int:
        """Remove all entities defined in a specific document.

        Used during incremental builds when a document is re-read.

        Args:
            docname: RST document name

        Returns:
            Number of entities removed
        """
        storage = self._get_storage()
        to_remove = [
            entity_id
            for entity_id, data in storage.items()
            if data.get("docname") == docname
        ]
        for entity_id in to_remove:
            del storage[entity_id]
        return len(to_remove)
