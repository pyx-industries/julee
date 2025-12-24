"""ContainerRepository protocol."""

from typing import Protocol, runtime_checkable

from julee.c4.entities.container import Container, ContainerType

from .base import BaseRepository


@runtime_checkable
class ContainerRepository(BaseRepository[Container], Protocol):
    """Repository protocol for Container entities.

    Extends BaseRepository with container-specific queries needed
    for C4 diagram generation.
    """

    async def get_by_system(self, system_slug: str) -> list[Container]:
        """Get all containers within a software system.

        Args:
            system_slug: Parent system slug

        Returns:
            List of containers in the system
        """
        ...

    async def get_by_type(self, container_type: ContainerType) -> list[Container]:
        """Get containers of a specific type.

        Args:
            container_type: web_application, database, etc.

        Returns:
            List of containers matching the type
        """
        ...

    async def get_data_stores(self, system_slug: str | None = None) -> list[Container]:
        """Get all data store containers.

        Args:
            system_slug: Optional filter by system

        Returns:
            List of database/storage containers
        """
        ...

    async def get_applications(self, system_slug: str | None = None) -> list[Container]:
        """Get all application containers (non-data-stores).

        Args:
            system_slug: Optional filter by system

        Returns:
            List of application containers
        """
        ...

    async def get_by_tag(self, tag: str) -> list[Container]:
        """Get containers with a specific tag.

        Args:
            tag: Tag to filter by (case-insensitive)

        Returns:
            List of containers with the tag
        """
        ...

    async def get_by_docname(self, docname: str) -> list[Container]:
        """Get containers defined in a specific document.

        Args:
            docname: Sphinx document name

        Returns:
            List of containers defined in that document
        """
        ...

    async def clear_by_docname(self, docname: str) -> int:
        """Clear containers defined in a specific document.

        Args:
            docname: Sphinx document name

        Returns:
            Number of containers removed
        """
        ...
