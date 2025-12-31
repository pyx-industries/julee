"""In-memory projection mapping repository implementation.

For testing and development. Not for production use.
"""

import fnmatch
from typing import Any

from julee.contrib.untp.entities.projection import ProjectionMapping


class MemoryProjectionMappingRepository:
    """In-memory repository for projection mapping configuration.

    Implements the ProjectionMappingRepository protocol for testing.
    """

    def __init__(self) -> None:
        self._mappings: dict[str, ProjectionMapping] = {}

    async def get(self, entity_id: str) -> ProjectionMapping | None:
        return self._mappings.get(entity_id)

    async def get_many(
        self, entity_ids: list[str]
    ) -> dict[str, ProjectionMapping | None]:
        return {eid: self._mappings.get(eid) for eid in entity_ids}

    async def save(self, entity: ProjectionMapping) -> None:
        self._mappings[entity.mapping_id] = entity

    async def list_all(self) -> list[ProjectionMapping]:
        return list(self._mappings.values())

    async def list_filtered(self, **filters: Any) -> list[ProjectionMapping]:
        return list(self._mappings.values())

    async def delete(self, entity_id: str) -> bool:
        if entity_id in self._mappings:
            del self._mappings[entity_id]
            return True
        return False

    async def clear(self) -> None:
        self._mappings.clear()

    async def list_slugs(self) -> set[str]:
        return set(self._mappings.keys())

    async def get_for_service_type(self, service_type: str) -> ProjectionMapping | None:
        """Get the projection mapping for a specific service type.

        Uses glob pattern matching against service_type_pattern.
        Returns the first matching mapping.
        """
        for mapping in self._mappings.values():
            if fnmatch.fnmatch(service_type, mapping.service_type_pattern):
                return mapping
        return None

    async def list_by_pattern_prefix(self, prefix: str) -> list[ProjectionMapping]:
        """Get all mappings with patterns starting with a prefix."""
        return [
            m
            for m in self._mappings.values()
            if m.service_type_pattern.startswith(prefix)
        ]
