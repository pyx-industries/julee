"""In-memory DynamicStep repository implementation."""

from julee.c4.entities.dynamic_step import DynamicStep
from julee.c4.entities.relationship import ElementType
from julee.c4.repositories.dynamic_step import DynamicStepRepository
from julee.core.infrastructure.repositories.memory.base import MemoryRepositoryMixin


class MemoryDynamicStepRepository(
    MemoryRepositoryMixin[DynamicStep], DynamicStepRepository
):
    """In-memory implementation of DynamicStepRepository.

    Stores dynamic steps in a dictionary keyed by slug.
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        self.storage: dict[str, DynamicStep] = {}
        self.entity_name = "DynamicStep"
        self.id_field = "slug"

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
            del self.storage[slug]
        return len(to_remove)
