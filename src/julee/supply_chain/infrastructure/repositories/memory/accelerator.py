"""Memory implementation of AcceleratorRepository."""

import logging

from julee.core.infrastructure.repositories.memory.base import MemoryRepositoryMixin
from julee.supply_chain.entities.accelerator import Accelerator
from julee.supply_chain.repositories.accelerator import AcceleratorRepository

logger = logging.getLogger(__name__)


class MemoryAcceleratorRepository(
    MemoryRepositoryMixin[Accelerator], AcceleratorRepository
):
    """In-memory implementation of AcceleratorRepository.

    Accelerators are stored in a dictionary keyed by slug. This implementation
    is used during Sphinx builds where accelerators are populated during doctree
    processing and support incremental builds via docname tracking.
    """

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.storage: dict[str, Accelerator] = {}
        self.entity_name = "Accelerator"
        self.id_field = "slug"

    # -------------------------------------------------------------------------
    # BaseRepository implementation (delegating to protected helpers)
    # -------------------------------------------------------------------------

    async def get(self, entity_id: str) -> Accelerator | None:
        """Get an accelerator by slug."""
        return self._get_entity(entity_id)

    async def get_many(self, entity_ids: list[str]) -> dict[str, Accelerator | None]:
        """Get multiple accelerators by slug."""
        return self._get_many_entities(entity_ids)

    async def save(self, entity: Accelerator) -> None:
        """Save an accelerator."""
        self._save_entity(entity)

    async def list_all(self) -> list[Accelerator]:
        """List all accelerators."""
        return self._list_all_entities()

    async def delete(self, entity_id: str) -> bool:
        """Delete an accelerator by slug."""
        return self._delete_entity(entity_id)

    async def clear(self) -> None:
        """Clear all accelerators."""
        self._clear_storage()

    # -------------------------------------------------------------------------
    # AcceleratorRepository-specific queries
    # -------------------------------------------------------------------------

    async def get_by_status(self, status: str) -> list[Accelerator]:
        """Get all accelerators with a specific status."""
        status_normalized = status.lower().strip()
        return [
            accel
            for accel in self.storage.values()
            if accel.status_normalized == status_normalized
        ]

    async def get_by_docname(self, docname: str) -> list[Accelerator]:
        """Get all accelerators defined in a specific document."""
        return [accel for accel in self.storage.values() if accel.docname == docname]

    async def clear_by_docname(self, docname: str) -> int:
        """Remove all accelerators defined in a specific document."""
        to_remove = [
            slug for slug, accel in self.storage.items() if accel.docname == docname
        ]
        for slug in to_remove:
            del self.storage[slug]
        return len(to_remove)

    async def get_by_integration(
        self, integration_slug: str, relationship: str
    ) -> list[Accelerator]:
        """Get accelerators that have a relationship with an integration."""
        result = []
        for accel in self.storage.values():
            if relationship == "sources_from":
                if integration_slug in accel.get_sources_from_slugs():
                    result.append(accel)
            elif relationship == "publishes_to":
                if integration_slug in accel.get_publishes_to_slugs():
                    result.append(accel)
        return result

    async def get_dependents(self, accelerator_slug: str) -> list[Accelerator]:
        """Get accelerators that depend on a specific accelerator."""
        return [
            accel
            for accel in self.storage.values()
            if accelerator_slug in accel.depends_on
        ]

    async def get_fed_by(self, accelerator_slug: str) -> list[Accelerator]:
        """Get accelerators that feed into a specific accelerator."""
        return [
            accel
            for accel in self.storage.values()
            if accelerator_slug in accel.feeds_into
        ]

    async def get_all_statuses(self) -> set[str]:
        """Get all unique statuses across all accelerators."""
        return {
            accel.status_normalized
            for accel in self.storage.values()
            if accel.status_normalized
        }

    async def list_slugs(self) -> set[str]:
        """List all accelerator slugs."""
        return self._list_slugs()

    async def list_filtered(
        self,
        solution_slug: str | None = None,
        status: str | None = None,
    ) -> list[Accelerator]:
        """List accelerators matching filters.

        Uses AND logic when multiple filters are provided.
        """
        results = list(self.storage.values())

        # Filter by solution
        if solution_slug is not None:
            results = [a for a in results if a.solution_slug == solution_slug]

        # Filter by status
        if status is not None:
            status_normalized = status.lower().strip()
            results = [a for a in results if a.status_normalized == status_normalized]

        return results
