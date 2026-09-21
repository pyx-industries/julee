"""Sync adapters for async repositories.

Sphinx directives are synchronous, but our domain repositories are async
(following julee patterns). This module provides adapters to bridge the gap.
"""

import asyncio
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from ..domain.repositories.base import BaseRepository

T = TypeVar("T", bound=BaseModel)


class SyncRepositoryAdapter(Generic[T]):
    """Synchronous wrapper for async repository methods.

    Provides a synchronous interface to async repositories for use in
    Sphinx directives. Uses asyncio.run() to execute async methods.

    Example:
        >>> async_repo = MemoryStoryRepository()
        >>> sync_repo = SyncRepositoryAdapter(async_repo)
        >>> story = sync_repo.get("my-story-slug")  # Sync call

    Note:
        This adapter is designed for use in Sphinx's synchronous directive
        system. The overhead of asyncio.run() is negligible for in-memory
        repositories.
    """

    def __init__(self, async_repo: BaseRepository[T]) -> None:
        """Initialize with an async repository.

        Args:
            async_repo: An async repository implementing BaseRepository[T]
        """
        self._repo = async_repo

    @property
    def async_repo(self) -> BaseRepository[T]:
        """Access the underlying async repository."""
        return self._repo

    def get(self, entity_id: str) -> T | None:
        """Retrieve an entity by ID (sync wrapper).

        Args:
            entity_id: Unique entity identifier

        Returns:
            Entity if found, None otherwise
        """
        return asyncio.run(self._repo.get(entity_id))

    def get_many(self, entity_ids: list[str]) -> dict[str, T | None]:
        """Retrieve multiple entities by ID (sync wrapper).

        Args:
            entity_ids: List of unique entity identifiers

        Returns:
            Dict mapping entity_id to entity (or None if not found)
        """
        return asyncio.run(self._repo.get_many(entity_ids))

    def save(self, entity: T) -> None:
        """Save an entity (sync wrapper).

        Args:
            entity: Complete entity to save
        """
        asyncio.run(self._repo.save(entity))

    def list_all(self) -> list[T]:
        """List all entities (sync wrapper).

        Returns:
            List of all entities in the repository
        """
        return asyncio.run(self._repo.list_all())

    def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID (sync wrapper).

        Args:
            entity_id: Unique entity identifier

        Returns:
            True if entity was deleted, False if not found
        """
        return asyncio.run(self._repo.delete(entity_id))

    def clear(self) -> None:
        """Remove all entities from the repository (sync wrapper)."""
        asyncio.run(self._repo.clear())

    def run_async(self, coro: Any) -> Any:
        """Run an arbitrary async method on the underlying repository.

        Useful for repository-specific methods not in BaseRepository.

        Args:
            coro: A coroutine to execute

        Returns:
            The result of the coroutine

        Example:
            >>> result = sync_repo.run_async(
            ...     sync_repo.async_repo.find_by_persona("Staff Member")
            ... )
        """
        return asyncio.run(coro)
