"""BoundedContext repository protocol.

Defines the interface for discovering and accessing bounded contexts
in a codebase. Implementations may read from the filesystem, from
cached state, or from other sources.
"""

from typing import Protocol, runtime_checkable

from julee.shared.entities import BoundedContext


@runtime_checkable
class BoundedContextRepository(Protocol):
    """Repository for bounded context discovery and access.

    Unlike typical CRUD repositories, this repository is primarily
    read-oriented - bounded contexts are defined by the filesystem
    structure, not created through the repository.

    The repository may filter results based on doctrinal configuration
    (reserved words, required structural markers, etc.).
    """

    async def list_all(self) -> list[BoundedContext]:
        """List all discovered bounded contexts.

        Returns:
            All bounded contexts that pass doctrinal filters
        """
        ...

    async def get(self, slug: str) -> BoundedContext | None:
        """Get a bounded context by its slug.

        Args:
            slug: The directory name / identifier

        Returns:
            BoundedContext if found, None otherwise
        """
        ...
