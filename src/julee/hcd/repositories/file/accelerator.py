"""File-backed implementation of AcceleratorRepository."""

import logging
from pathlib import Path

from ...domain.models.accelerator import Accelerator
from ...domain.repositories.accelerator import AcceleratorRepository
from ...parsers.rst import scan_accelerator_directory
from ...serializers.rst import serialize_accelerator
from .base import FileRepositoryMixin

logger = logging.getLogger(__name__)


class FileAcceleratorRepository(
    FileRepositoryMixin[Accelerator], AcceleratorRepository
):
    """File-backed implementation of AcceleratorRepository.

    Accelerators are stored as RST files with define-accelerator directives:
    {base_path}/{accelerator_slug}.rst
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize with base path for accelerator RST files.

        Args:
            base_path: Root directory for accelerator files (e.g., docs/accelerators/)
        """
        self.base_path = Path(base_path)
        self.storage: dict[str, Accelerator] = {}
        self.entity_name = "Accelerator"
        self.id_field = "slug"

        # Load existing accelerators from disk
        self._load_all()

    def _get_file_path(self, entity: Accelerator) -> Path:
        """Get file path for an accelerator."""
        return self.base_path / f"{entity.slug}.rst"

    def _serialize(self, entity: Accelerator) -> str:
        """Serialize accelerator to RST format."""
        return serialize_accelerator(entity)

    def _load_all(self) -> None:
        """Load all accelerators from RST files."""
        if not self.base_path.exists():
            logger.info(f"Accelerators directory not found: {self.base_path}")
            return

        accelerators = scan_accelerator_directory(self.base_path)
        for accelerator in accelerators:
            self.storage[accelerator.slug] = accelerator

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
                if any(ref.slug == integration_slug for ref in accel.sources_from):
                    result.append(accel)
            elif relationship == "publishes_to":
                if any(ref.slug == integration_slug for ref in accel.publishes_to):
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
