"""DynamicStepRepository protocol."""

from typing import Protocol, runtime_checkable

from julee.c4.entities.dynamic_step import DynamicStep
from julee.c4.entities.relationship import ElementType

from .base import BaseRepository


@runtime_checkable
class DynamicStepRepository(BaseRepository[DynamicStep], Protocol):
    """Repository protocol for DynamicStep entities.

    Extends BaseRepository with dynamic-diagram-specific queries
    for generating sequence/interaction diagrams.
    """

    async def get_by_sequence(self, sequence_name: str) -> list[DynamicStep]:
        """Get all steps in a sequence, ordered by step_number.

        Args:
            sequence_name: Name of the sequence/scenario

        Returns:
            List of steps in order
        """
        ...

    async def get_sequences(self) -> list[str]:
        """Get all unique sequence names.

        Returns:
            List of sequence names
        """
        ...

    async def get_for_element(
        self,
        element_type: ElementType,
        element_slug: str,
    ) -> list[DynamicStep]:
        """Get all steps involving an element.

        Args:
            element_type: Type of element
            element_slug: Element's slug

        Returns:
            List of steps involving the element
        """
        ...

    async def get_step(
        self, sequence_name: str, step_number: int
    ) -> DynamicStep | None:
        """Get a specific step by sequence and number.

        Args:
            sequence_name: Name of the sequence
            step_number: Step number (1-based)

        Returns:
            The step if found, None otherwise
        """
        ...

    async def get_by_docname(self, docname: str) -> list[DynamicStep]:
        """Get steps defined in a specific document.

        Args:
            docname: Sphinx document name

        Returns:
            List of steps defined in that document
        """
        ...

    async def clear_by_docname(self, docname: str) -> int:
        """Clear steps defined in a specific document.

        Args:
            docname: Sphinx document name

        Returns:
            Number of steps removed
        """
        ...
