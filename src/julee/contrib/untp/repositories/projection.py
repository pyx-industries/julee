"""ProjectionMappingRepository protocol.

Defines the interface for storing projection configuration.
"""

from typing import Protocol, runtime_checkable

from julee.core.repositories.base import BaseRepository
from julee.contrib.untp.entities.projection import ProjectionMapping


@runtime_checkable
class ProjectionMappingRepository(BaseRepository[ProjectionMapping], Protocol):
    """Repository protocol for projection mapping configuration.

    Stores custom projection mappings that control how operations
    are projected to UNTP events.
    """

    async def get_for_service_type(
        self, service_type: str
    ) -> ProjectionMapping | None:
        """Get the projection mapping for a specific service type.

        Uses pattern matching against service_type_pattern.

        Args:
            service_type: Fully qualified service type name

        Returns:
            The matching projection mapping, or None if no match
        """
        ...

    async def list_by_pattern_prefix(
        self, prefix: str
    ) -> list[ProjectionMapping]:
        """Get all mappings with patterns starting with a prefix.

        Args:
            prefix: Pattern prefix to match (e.g., 'myapp.services.')

        Returns:
            List of mappings with patterns starting with this prefix
        """
        ...
