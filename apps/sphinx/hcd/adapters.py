"""Sync adapters for async repositories.

Sphinx directives are synchronous, but our domain repositories are async
(following julee patterns). This module provides adapters to bridge the gap.
"""

import asyncio
import warnings
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from julee.core.repositories.base import BaseRepository

T = TypeVar("T", bound=BaseModel)


def _adapter_deprecation_warning(method_name: str) -> None:
    """Emit deprecation warning for direct adapter method access."""
    warnings.warn(
        f"Direct adapter method '{method_name}()' is deprecated. "
        f"Use the corresponding use case instead (e.g., list_*, get_*, create_*).",
        DeprecationWarning,
        stacklevel=3,
    )


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
        """DEPRECATED: Use the corresponding get_* use case instead.

        Retrieve an entity by ID (sync wrapper).

        Args:
            entity_id: Unique entity identifier

        Returns:
            Entity if found, None otherwise
        """
        _adapter_deprecation_warning("get")
        return asyncio.run(self._repo.get(entity_id))

    def get_many(self, entity_ids: list[str]) -> dict[str, T | None]:
        """DEPRECATED: Use the corresponding get_* use case instead.

        Retrieve multiple entities by ID (sync wrapper).

        Args:
            entity_ids: List of unique entity identifiers

        Returns:
            Dict mapping entity_id to entity (or None if not found)
        """
        _adapter_deprecation_warning("get_many")
        return asyncio.run(self._repo.get_many(entity_ids))

    def save(self, entity: T) -> None:
        """DEPRECATED: Use the corresponding create_* use case instead.

        Save an entity (sync wrapper).

        Args:
            entity: Complete entity to save
        """
        _adapter_deprecation_warning("save")
        asyncio.run(self._repo.save(entity))

    def list_all(self) -> list[T]:
        """DEPRECATED: Use the corresponding list_* use case instead.

        List all entities (sync wrapper).

        Returns:
            List of all entities in the repository
        """
        _adapter_deprecation_warning("list_all")
        return asyncio.run(self._repo.list_all())

    def delete(self, entity_id: str) -> bool:
        """DEPRECATED: Use the corresponding delete_* use case instead.

        Delete an entity by ID (sync wrapper).

        Args:
            entity_id: Unique entity identifier

        Returns:
            True if entity was deleted, False if not found
        """
        _adapter_deprecation_warning("delete")
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
