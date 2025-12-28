"""Sphinx environment repository mixin for C4 entities.

Provides common functionality for repositories that store C4 data in
Sphinx's BuildEnvironment for parallel-safe builds.
"""

import logging
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


def pluralize(name: str) -> str:
    """Pluralize an entity name for storage key.

    Args:
        name: Singular entity name (e.g., "Container")

    Returns:
        Plural form (e.g., "containers")
    """
    lower = name.lower()
    if lower.endswith("y") and len(lower) > 1 and lower[-2] not in "aeiou":
        return lower[:-1] + "ies"
    elif lower.endswith("s") or lower.endswith("x") or lower.endswith("ch"):
        return lower + "es"
    else:
        return lower + "s"


def derive_entity_config(entity_class: type, entity_key: str | None = None) -> dict:
    """Derive configuration from entity class.

    Args:
        entity_class: Pydantic model class
        entity_key: Optional explicit key override

    Returns:
        Dict with entity_name, entity_key
    """
    entity_name = entity_class.__name__
    if entity_key is None:
        entity_key = pluralize(entity_name)

    return {
        "entity_name": entity_name,
        "entity_key": entity_key,
    }


class SphinxEnvC4RepositoryMixin(Generic[T]):
    """Mixin for C4 repositories storing data in Sphinx env.

    Stores entities as serialized dicts in env.c4_storage[entity_key].
    This enables parallel builds since env is properly pickled between
    worker processes and merged back via env-merge-info event.

    Subclasses must define entity_class as a class attribute.
    """

    entity_class: ClassVar[type[T]]
    entity_name: ClassVar[str] = ""
    entity_key: ClassVar[str] = ""
    id_field: ClassVar[str] = "slug"

    env: "BuildEnvironment"

    def __init__(self, env: "BuildEnvironment") -> None:
        """Initialize with Sphinx build environment."""
        self.env = env

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Configure entity metadata when subclass is created."""
        super().__init_subclass__(**kwargs)

        if not hasattr(cls, "entity_class") or cls.entity_class is None:
            return

        config = derive_entity_config(cls.entity_class, cls.entity_key or None)

        if not cls.entity_name:
            cls.entity_name = config["entity_name"]
        if not cls.entity_key:
            cls.entity_key = config["entity_key"]

    def _get_storage(self) -> dict[str, dict[str, Any]]:
        """Get or create storage dict for this entity type.

        Storage is located at env.c4_storage[entity_key].
        """
        if not hasattr(self.env, "c4_storage"):
            self.env.c4_storage = {}
        if self.entity_key not in self.env.c4_storage:
            self.env.c4_storage[self.entity_key] = {}
        return self.env.c4_storage[self.entity_key]

    def _get_entity_id(self, entity: T) -> str:
        """Extract entity ID from entity instance."""
        return getattr(entity, self.id_field)

    def _serialize(self, entity: T) -> dict[str, Any]:
        """Serialize entity to picklable dict."""
        return entity.model_dump()

    def _deserialize(self, data: dict[str, Any]) -> T:
        """Reconstruct entity from serialized dict."""
        return self.entity_class(**data)

    async def get(self, entity_id: str) -> T | None:
        """Retrieve entity by ID."""
        storage = self._get_storage()
        data = storage.get(entity_id)
        if data is None:
            return None
        return self._deserialize(data)

    async def get_many(self, entity_ids: list[str]) -> dict[str, T | None]:
        """Retrieve multiple entities by ID."""
        storage = self._get_storage()
        result: dict[str, T | None] = {}
        for entity_id in entity_ids:
            data = storage.get(entity_id)
            result[entity_id] = self._deserialize(data) if data else None
        return result

    async def save(self, entity: T) -> None:
        """Save entity to storage."""
        entity_id = self._get_entity_id(entity)
        storage = self._get_storage()
        storage[entity_id] = self._serialize(entity)

    async def list_all(self) -> list[T]:
        """List all entities."""
        storage = self._get_storage()
        return [self._deserialize(data) for data in storage.values()]

    async def delete(self, entity_id: str) -> bool:
        """Delete entity by ID."""
        storage = self._get_storage()
        if entity_id in storage:
            del storage[entity_id]
            return True
        return False

    async def clear(self) -> None:
        """Remove all entities from storage."""
        storage = self._get_storage()
        storage.clear()

    async def find_by_field(self, field: str, value: Any) -> list[T]:
        """Find all entities where field equals value."""
        storage = self._get_storage()
        return [
            self._deserialize(data)
            for data in storage.values()
            if data.get(field) == value
        ]

    async def get_by_docname(self, docname: str) -> list[T]:
        """Get entities defined in a specific document."""
        return await self.find_by_field("docname", docname)

    async def clear_by_docname(self, docname: str) -> int:
        """Remove all entities defined in a specific document."""
        storage = self._get_storage()
        to_remove = [
            entity_id
            for entity_id, data in storage.items()
            if data.get("docname") == docname
        ]
        for entity_id in to_remove:
            del storage[entity_id]
        return len(to_remove)
