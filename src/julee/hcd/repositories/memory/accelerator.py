"""Memory implementation of AcceleratorRepository."""

import logging

from ...domain.models.accelerator import Accelerator
from ...domain.repositories.accelerator import AcceleratorRepository
from .base import MemoryRepositoryMixin

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
