"""ComponentRepository protocol."""

from typing import Protocol, runtime_checkable

from julee.c4.entities.component import Component

from .base import BaseRepository


@runtime_checkable
class ComponentRepository(BaseRepository[Component], Protocol):
    """Repository protocol for Component entities.

    Extends BaseRepository with component-specific queries needed
    for C4 diagram generation.
    """

    async def get_by_container(self, container_slug: str) -> list[Component]:
        """Get all components within a container.

        Args:
            container_slug: Parent container slug

        Returns:
            List of components in the container
        """
        ...

    async def get_by_system(self, system_slug: str) -> list[Component]:
        """Get all components within a software system.

        Args:
            system_slug: System slug

        Returns:
            List of components across all containers in the system
        """
        ...

    async def get_with_code(self) -> list[Component]:
        """Get components that have linked code paths.

        Returns:
            List of components with code_path set
        """
        ...

    async def get_by_tag(self, tag: str) -> list[Component]:
        """Get components with a specific tag.

        Args:
            tag: Tag to filter by (case-insensitive)

        Returns:
            List of components with the tag
        """
        ...

    async def get_by_docname(self, docname: str) -> list[Component]:
        """Get components defined in a specific document.

        Args:
            docname: Sphinx document name

        Returns:
            List of components defined in that document
        """
        ...

    async def clear_by_docname(self, docname: str) -> int:
        """Clear components defined in a specific document.

        Args:
            docname: Sphinx document name

        Returns:
            Number of components removed
        """
        ...
