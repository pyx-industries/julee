"""IntegrationRepository protocol.

Defines the interface for integration data access.
"""

from typing import Protocol, runtime_checkable

from julee.core.repositories.base import BaseRepository
from julee.hcd.entities.integration import Direction, Integration


@runtime_checkable
class IntegrationRepository(BaseRepository[Integration], Protocol):
    """Repository protocol for Integration entities.

    Extends BaseRepository with integration-specific query methods.
    Integrations are indexed from YAML manifests and are read-only during
    a Sphinx build (populated at builder-inited, queried during rendering).
    """

    async def get_by_direction(self, direction: Direction) -> list[Integration]:
        """Get all integrations with a specific data flow direction.

        Args:
            direction: Direction to filter by

        Returns:
            List of integrations matching the direction
        """
        ...

    async def get_by_module(self, module: str) -> Integration | None:
        """Get an integration by its module name.

        Args:
            module: Python module name (e.g., "pilot_data_collection")

        Returns:
            Integration if found, None otherwise
        """
        ...

    async def get_by_name(self, name: str) -> Integration | None:
        """Get an integration by its display name (case-insensitive).

        Args:
            name: Display name to search for

        Returns:
            Integration if found, None otherwise
        """
        ...

    async def get_all_directions(self) -> set[Direction]:
        """Get all unique directions that have integrations.

        Returns:
            Set of directions with at least one integration
        """
        ...

    async def get_with_dependencies(self) -> list[Integration]:
        """Get all integrations that have external dependencies.

        Returns:
            List of integrations with non-empty depends_on list
        """
        ...

    async def get_by_dependency(self, dep_name: str) -> list[Integration]:
        """Get all integrations that depend on a specific external system.

        Args:
            dep_name: External dependency name (case-insensitive)

        Returns:
            List of integrations that have this dependency
        """
        ...

    async def list_filtered(
        self,
        solution_slug: str | None = None,
    ) -> list[Integration]:
        """List integrations matching filters.

        Filter parameters declared here are automatically surfaced as
        FastAPI query params via make_list_request(). Implementations
        should use AND logic when multiple filters are provided.

        Args:
            solution_slug: Filter to integrations for this solution

        Returns:
            List of integrations matching all provided filters
        """
        ...
