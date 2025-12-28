"""SphinxEnv implementation of DynamicStepRepository."""

from julee.c4.entities.dynamic_step import DynamicStep
from julee.c4.entities.relationship import ElementType
from julee.c4.repositories.dynamic_step import DynamicStepRepository

from .base import SphinxEnvC4RepositoryMixin


class SphinxEnvDynamicStepRepository(
    SphinxEnvC4RepositoryMixin[DynamicStep], DynamicStepRepository
):
    """SphinxEnv implementation of DynamicStepRepository."""

    entity_class = DynamicStep

    async def get_by_sequence(self, sequence_name: str) -> list[DynamicStep]:
        """Get all steps in a sequence, ordered by step_number."""
        steps = await self.find_by_field("sequence_name", sequence_name)
        return sorted(steps, key=lambda s: s.step_number)

    async def get_sequences(self) -> list[str]:
        """Get all unique sequence names."""
        all_steps = await self.list_all()
        return list(set(s.sequence_name for s in all_steps))

    async def get_for_element(
        self, element_type: ElementType, element_slug: str
    ) -> list[DynamicStep]:
        """Get all steps involving an element."""
        all_steps = await self.list_all()
        return [
            s for s in all_steps
            if (s.source_type == element_type and s.source_slug == element_slug)
            or (s.destination_type == element_type and s.destination_slug == element_slug)
        ]

    async def get_step(
        self, sequence_name: str, step_number: int
    ) -> DynamicStep | None:
        """Get a specific step by sequence and number."""
        steps = await self.get_by_sequence(sequence_name)
        for step in steps:
            if step.step_number == step_number:
                return step
        return None
