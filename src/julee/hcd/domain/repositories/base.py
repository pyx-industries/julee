"""Base repository protocol for sphinx_hcd.

Defines the generic repository interface following julee clean architecture
patterns. All repository operations are async for consistency with julee,
with sync adapters provided in the sphinx/ application layer.
"""

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class BaseRepository(Protocol[T]):
    """Generic base repository protocol for HCD entities.

    This protocol defines the common interface shared by all domain
    repositories in sphinx_hcd. It uses generics to provide type safety
    while eliminating code duplication.

    Type Parameter:
        T: The domain entity type (must extend Pydantic BaseModel)

    All methods are async for consistency with julee patterns. The sphinx/
    application layer provides SyncRepositoryAdapter for use in Sphinx
    directives which are synchronous.
    """

    async def get(self, entity_id: str) -> T | None:
        """Retrieve an entity by ID.

        Args:
            entity_id: Unique entity identifier (typically a slug)

        Returns:
            Entity if found, None otherwise
        """
        ...

    async def get_many(self, entity_ids: list[str]) -> dict[str, T | None]:
        """Retrieve multiple entities by ID.

        Args:
            entity_ids: List of unique entity identifiers

        Returns:
            Dict mapping entity_id to entity (or None if not found)
        """
        ...

    async def save(self, entity: T) -> None:
        """Save an entity.

        Args:
            entity: Complete entity to save

        Note:
            Must be idempotent - saving the same entity state is safe.
        """
        ...

    async def list_all(self) -> list[T]:
        """List all entities.

        Returns:
            List of all entities in the repository
        """
        ...

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID.

        Args:
            entity_id: Unique entity identifier

        Returns:
            True if entity was deleted, False if not found
        """
        ...

    async def clear(self) -> None:
        """Remove all entities from the repository.

        Used primarily for testing and re-initialization during
        Sphinx incremental builds.
        """
        ...
