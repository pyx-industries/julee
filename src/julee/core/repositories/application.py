"""Application repository protocol.

Defines the interface for discovering and accessing applications
in a codebase. Implementations may read from the filesystem, from
cached state, or from other sources.
"""

from typing import Protocol, runtime_checkable

from julee.core.entities.application import Application, AppType


@runtime_checkable
class ApplicationRepository(Protocol):
    """Repository for application discovery and access.

    Unlike typical CRUD repositories, this repository is primarily
    read-oriented - applications are defined by the filesystem
    structure, not created through the repository.

    The repository may filter results based on doctrinal configuration
    (reserved directories, required structural markers, etc.).
    """

    async def list_all(self) -> list[Application]:
        """List all discovered applications.

        Returns:
            All applications in the solution's apps/ directory
        """
        ...

    async def get(self, slug: str) -> Application | None:
        """Get an application by its slug.

        Args:
            slug: The directory name / identifier

        Returns:
            Application if found, None otherwise
        """
        ...

    async def list_by_type(self, app_type: AppType) -> list[Application]:
        """List applications of a specific type.

        Args:
            app_type: The application type to filter by

        Returns:
            Applications matching the specified type
        """
        ...
