"""Memory repository base classes and mixins for sphinx_hcd.

Provides common functionality for in-memory repository implementations,
following julee patterns but simplified for sphinx_hcd's needs.
"""

import logging
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class MemoryRepositoryMixin(Generic[T]):
    """Mixin providing common repository patterns for memory implementations.

    Encapsulates common functionality used across all memory repository
    implementations:
    - Dictionary-based entity storage and retrieval
    - Standardized logging patterns
    - Generic CRUD operations

    Classes using this mixin must provide:
    - self.storage: dict[str, T] for entity storage
    - self.entity_name: str for logging
    - self.id_field: str naming the entity's ID field
    """

    storage: dict[str, T]
    entity_name: str
    id_field: str

    def _get_entity_id(self, entity: T) -> str:
        """Extract the entity ID from an entity instance."""
        return getattr(entity, self.id_field)

    async def get(self, entity_id: str) -> T | None:
        """Retrieve an entity by ID."""
        entity = self.storage.get(entity_id)
        if entity is None:
            logger.debug(
                f"Memory{self.entity_name}Repository: {self.entity_name} not found",
                extra={f"{self.entity_name.lower()}_id": entity_id},
            )
        return entity

    async def get_many(self, entity_ids: list[str]) -> dict[str, T | None]:
        """Retrieve multiple entities by ID."""
        result: dict[str, T | None] = {}
        for entity_id in entity_ids:
            result[entity_id] = self.storage.get(entity_id)
        return result

    async def save(self, entity: T) -> None:
        """Save an entity to storage."""
        entity_id = self._get_entity_id(entity)
        self.storage[entity_id] = entity
        logger.debug(
            f"Memory{self.entity_name}Repository: Saved {self.entity_name}",
            extra={f"{self.entity_name.lower()}_id": entity_id},
        )

    async def list_all(self) -> list[T]:
        """List all entities."""
        return list(self.storage.values())

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        if entity_id in self.storage:
            del self.storage[entity_id]
            logger.debug(
                f"Memory{self.entity_name}Repository: Deleted {self.entity_name}",
                extra={f"{self.entity_name.lower()}_id": entity_id},
            )
            return True
        return False

    async def clear(self) -> None:
        """Remove all entities from storage."""
        count = len(self.storage)
        self.storage.clear()
        logger.debug(
            f"Memory{self.entity_name}Repository: Cleared {count} entities",
        )

    # Additional query methods that subclasses can use

    async def find_by_field(self, field: str, value: Any) -> list[T]:
        """Find all entities where field equals value."""
        return [
            entity
            for entity in self.storage.values()
            if getattr(entity, field, None) == value
        ]

    async def find_by_field_in(self, field: str, values: list[Any]) -> list[T]:
        """Find all entities where field is in values."""
        value_set = set(values)
        return [
            entity
            for entity in self.storage.values()
            if getattr(entity, field, None) in value_set
        ]
