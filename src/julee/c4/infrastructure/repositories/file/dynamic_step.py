"""File-backed DynamicStep repository implementation."""

import logging
from pathlib import Path

from julee.c4.entities.dynamic_step import DynamicStep
from julee.c4.entities.relationship import ElementType
from julee.c4.parsers.rst import scan_dynamic_step_directory
from julee.c4.repositories.dynamic_step import DynamicStepRepository
from julee.c4.serializers.rst import serialize_dynamic_step

from .base import FileRepositoryMixin

logger = logging.getLogger(__name__)


class FileDynamicStepRepository(
    FileRepositoryMixin[DynamicStep], DynamicStepRepository
):
    """File-backed implementation of DynamicStepRepository.

    Stores dynamic steps as RST files with define-dynamic-step directives.
    File structure: {base_path}/{slug}.rst
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize repository with base path.

        Args:
            base_path: Directory to store dynamic step RST files
        """
        self.base_path = base_path
        self.storage: dict[str, DynamicStep] = {}
        self.entity_name = "DynamicStep"
        self.id_field = "slug"
        self._load_all()

    def _get_file_path(self, entity: DynamicStep) -> Path:
        """Get file path for a dynamic step."""
        return self.base_path / f"{entity.slug}.rst"

    def _serialize(self, entity: DynamicStep) -> str:
        """Serialize dynamic step to RST format."""
        return serialize_dynamic_step(entity)

    def _load_all(self) -> None:
        """Load all dynamic steps from disk."""
        if not self.base_path.exists():
            logger.debug(
                f"FileDynamicStepRepository: Base path does not exist: {self.base_path}"
            )
            return

        steps = scan_dynamic_step_directory(self.base_path)
        for step in steps:
            self.storage[step.slug] = step

    async def get_by_sequence(self, sequence_name: str) -> list[DynamicStep]:
        """Get all steps in a sequence, ordered by step_number."""
        steps = [s for s in self.storage.values() if s.sequence_name == sequence_name]
        return sorted(steps, key=lambda s: s.step_number)

    async def get_sequences(self) -> list[str]:
        """Get all unique sequence names."""
        return list({s.sequence_name for s in self.storage.values()})

    async def get_for_element(
        self,
        element_type: ElementType,
        element_slug: str,
    ) -> list[DynamicStep]:
        """Get all steps involving an element."""
        return [
            s
            for s in self.storage.values()
            if s.involves_element(element_type, element_slug)
        ]

    async def get_step(
        self, sequence_name: str, step_number: int
    ) -> DynamicStep | None:
        """Get a specific step by sequence and number."""
        for step in self.storage.values():
            if step.sequence_name == sequence_name and step.step_number == step_number:
                return step
        return None

    async def get_by_docname(self, docname: str) -> list[DynamicStep]:
        """Get steps defined in a specific document."""
        return [s for s in self.storage.values() if s.docname == docname]

    async def clear_by_docname(self, docname: str) -> int:
        """Clear steps defined in a specific document."""
        to_remove = [slug for slug, s in self.storage.items() if s.docname == docname]
        for slug in to_remove:
            await self.delete(slug)
        return len(to_remove)
