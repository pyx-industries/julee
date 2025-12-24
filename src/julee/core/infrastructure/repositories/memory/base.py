"""Memory repository base classes and mixins.

Provides common functionality for in-memory repository implementations,
following clean architecture patterns.

All methods are protected helpers (prefixed with _). Repository implementations
decide which operations to expose in their public API by delegating to these
helpers. This ensures repositories have full control over their contract.

Example usage:
    class MemoryDocumentRepository(MemoryRepositoryMixin[Document]):
        def __init__(self):
            self.storage: dict[str, Document] = {}
            self.entity_name = "Document"
            self.id_field = "document_id"

        async def get(self, doc_id: str) -> Document | None:
            return self._get_entity(doc_id)

        async def save(self, doc: Document) -> None:
            self._save_entity(doc)

        async def generate_id(self) -> str:
            return self._generate_id("doc")

        # No delete() - documents are immutable
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

_module_logger = logging.getLogger(__name__)


class MemoryRepositoryMixin(Generic[T]):
    """Mixin providing protected helper methods for memory repository implementations.

    All methods are protected (prefixed with _) to give repositories full control
    over their public API. Repositories implement their interface by delegating
    to these helpers.

    Required attributes (set in __init__):
        storage: dict[str, T] - Dictionary for entity storage
        entity_name: str - Name for logging (e.g., "Document")
        id_field: str - Name of the entity's ID field (e.g., "document_id")

    Optional attributes:
        logger: logging.Logger - Instance logger (defaults to module logger)
    """

    storage: dict[str, T]
    entity_name: str
    id_field: str
    logger: logging.Logger | None = None

    @property
    def _logger(self) -> logging.Logger:
        """Get logger, preferring instance logger if set."""
        return self.logger if self.logger is not None else _module_logger

    def _get_entity_id(self, entity: T) -> str:
        """Extract the entity ID from an entity instance."""
        return getattr(entity, self.id_field)

    # -------------------------------------------------------------------------
    # Core CRUD helpers
    # -------------------------------------------------------------------------

    def _get_entity(self, entity_id: str) -> T | None:
        """Retrieve an entity by ID.

        Args:
            entity_id: Unique entity identifier

        Returns:
            Entity if found, None otherwise
        """
        entity = self.storage.get(entity_id)
        if entity is None:
            self._logger.debug(
                f"Memory{self.entity_name}Repository: {self.entity_name} not found",
                extra={f"{self.entity_name.lower()}_id": entity_id},
            )
        return entity

    def _get_many_entities(self, entity_ids: list[str]) -> dict[str, T | None]:
        """Retrieve multiple entities by ID.

        Args:
            entity_ids: List of unique entity identifiers

        Returns:
            Dict mapping entity_id to entity (or None if not found)
        """
        result: dict[str, T | None] = {}
        for entity_id in entity_ids:
            result[entity_id] = self.storage.get(entity_id)
        return result

    def _save_entity(self, entity: T, update_timestamps: bool = True) -> None:
        """Save an entity to storage.

        Args:
            entity: Entity to save
            update_timestamps: Whether to update created_at/updated_at fields
        """
        if update_timestamps:
            self._update_timestamps(entity)

        entity_id = self._get_entity_id(entity)
        self.storage[entity_id] = entity

        log_extra = {f"{self.entity_name.lower()}_id": entity_id}
        self._add_log_extras(entity, log_extra)
        self._logger.debug(
            f"Memory{self.entity_name}Repository: Saved {self.entity_name}",
            extra=log_extra,
        )

    def _list_all_entities(self) -> list[T]:
        """List all entities in storage.

        Returns:
            List of all entities
        """
        return list(self.storage.values())

    # -------------------------------------------------------------------------
    # Destructive helpers (opt-in by exposing in your repo)
    # -------------------------------------------------------------------------

    def _delete_entity(self, entity_id: str) -> bool:
        """Delete an entity by ID.

        Args:
            entity_id: Unique entity identifier

        Returns:
            True if entity was deleted, False if not found
        """
        if entity_id in self.storage:
            del self.storage[entity_id]
            self._logger.debug(
                f"Memory{self.entity_name}Repository: Deleted {self.entity_name}",
                extra={f"{self.entity_name.lower()}_id": entity_id},
            )
            return True
        return False

    def _clear_storage(self) -> int:
        """Remove all entities from storage.

        Returns:
            Number of entities that were cleared
        """
        count = len(self.storage)
        self.storage.clear()
        self._logger.debug(
            f"Memory{self.entity_name}Repository: Cleared {count} entities",
        )
        return count

    # -------------------------------------------------------------------------
    # ID generation
    # -------------------------------------------------------------------------

    def _generate_id(self, prefix: str | None = None) -> str:
        """Generate a unique entity ID.

        Args:
            prefix: Optional prefix (defaults to entity_name.lower())

        Returns:
            Unique ID string in format "{prefix}-{uuid}"
        """
        if prefix is None:
            prefix = self.entity_name.lower()

        entity_id = f"{prefix}-{uuid.uuid4()}"

        self._logger.debug(
            f"Memory{self.entity_name}Repository: Generated ID",
            extra={f"{self.entity_name.lower()}_id": entity_id},
        )

        return entity_id

    # -------------------------------------------------------------------------
    # Timestamp management
    # -------------------------------------------------------------------------

    def _update_timestamps(self, entity: T) -> None:
        """Update created_at/updated_at timestamps on an entity.

        Sets created_at if it's None (new entity).
        Always updates updated_at if the field exists.

        Args:
            entity: Entity to update (modified in place)
        """
        now = datetime.now(timezone.utc)

        # Set created_at if None (new entity)
        if (
            hasattr(entity, "created_at")
            and getattr(entity, "created_at", None) is None
        ):
            # Pydantic models may need object.__setattr__ for frozen models
            try:
                entity.created_at = now
            except AttributeError:
                object.__setattr__(entity, "created_at", now)

        # Always update updated_at
        if hasattr(entity, "updated_at"):
            try:
                entity.updated_at = now
            except AttributeError:
                object.__setattr__(entity, "updated_at", now)

    # -------------------------------------------------------------------------
    # Query helpers
    # -------------------------------------------------------------------------

    def _find_by_field(self, field: str, value: Any) -> list[T]:
        """Find all entities where field equals value.

        Args:
            field: Field name to match
            value: Value to match

        Returns:
            List of matching entities
        """
        return [
            entity
            for entity in self.storage.values()
            if getattr(entity, field, None) == value
        ]

    def _find_by_field_in(self, field: str, values: list[Any]) -> list[T]:
        """Find all entities where field is in values.

        Args:
            field: Field name to match
            values: List of values to match

        Returns:
            List of matching entities
        """
        value_set = set(values)
        return [
            entity
            for entity in self.storage.values()
            if getattr(entity, field, None) in value_set
        ]

    # -------------------------------------------------------------------------
    # Public async query methods (for convenience in repositories)
    # -------------------------------------------------------------------------

    async def find_by_field(self, field: str, value: Any) -> list[T]:
        """Find all entities where field equals value.

        Async wrapper around _find_by_field for repository interface compatibility.

        Args:
            field: Field name to match
            value: Value to match

        Returns:
            List of matching entities
        """
        return self._find_by_field(field, value)

    async def find_by_field_in(self, field: str, values: list[Any]) -> list[T]:
        """Find all entities where field is in values.

        Async wrapper around _find_by_field_in for repository interface compatibility.

        Args:
            field: Field name to match
            values: List of values to match

        Returns:
            List of matching entities
        """
        return self._find_by_field_in(field, values)

    # -------------------------------------------------------------------------
    # Logging hooks (override in subclass for entity-specific logging)
    # -------------------------------------------------------------------------

    def _add_log_extras(self, entity: T, log_data: dict[str, Any]) -> None:
        """Add entity-specific data to log entries.

        Override this method to add domain-specific logging information.

        Args:
            entity: The entity being logged
            log_data: Dictionary to add logging data to (modified in place)
        """
        # Default: add status if present
        if hasattr(entity, "status"):
            status = entity.status
            log_data["status"] = (
                status.value if hasattr(status, "value") else str(status)
            )
