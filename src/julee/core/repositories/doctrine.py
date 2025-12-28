"""Doctrine repository protocol.

Defines the interface for extracting and accessing doctrine rules.
The primary implementation reads doctrine FROM test files - the tests
ARE the doctrine, this repository is a projection, not a separate store.

This preserves the single-source-of-truth principle: change a test
docstring, and the rule changes. The repository just reads what's there.
"""

from typing import Protocol, runtime_checkable

from julee.core.entities.doctrine import (
    DoctrineArea,
    DoctrineRule,
)


@runtime_checkable
class DoctrineRepository(Protocol):
    """Repository for doctrine rule extraction and access.

    Unlike typical CRUD repositories, this repository is read-only -
    doctrine rules are defined by test files, not created through
    the repository. Writing doctrine means writing tests.

    The repository extracts:
    - DoctrineRule from test method docstrings
    - DoctrineCategory from test class docstrings
    - DoctrineArea from test file names (mapping to entity types)
    - Entity definitions from julee.core.entities docstrings
    """

    async def list_rules(self, area: str | None = None) -> list[DoctrineRule]:
        """List all doctrine rules, optionally filtered by area.

        Args:
            area: Optional area slug to filter by (e.g., "bounded_context")

        Returns:
            All matching doctrine rules
        """
        ...

    async def list_areas(self) -> list[DoctrineArea]:
        """List all doctrine areas with their rules.

        Returns:
            All doctrine areas, each containing their categories and rules
        """
        ...

    async def get_area(self, slug: str) -> DoctrineArea | None:
        """Get a specific doctrine area by slug.

        Args:
            slug: The area identifier (e.g., "bounded_context")

        Returns:
            DoctrineArea if found, None otherwise
        """
        ...
