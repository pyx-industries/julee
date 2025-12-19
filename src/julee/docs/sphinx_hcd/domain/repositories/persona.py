"""PersonaRepository protocol.

Defines the interface for persona data access.
"""

from typing import Protocol, runtime_checkable

from ..models.persona import Persona
from .base import BaseRepository


@runtime_checkable
class PersonaRepository(BaseRepository[Persona], Protocol):
    """Repository protocol for Persona entities.

    Extends BaseRepository with persona-specific query methods.
    Personas are defined in RST documents and support incremental builds
    via docname tracking.

    Note: The base repository get() method uses slug as the identifier.
    Use get_by_name() or get_by_normalized_name() to find personas by
    their display name (as used in Gherkin stories).
    """

    async def get_by_name(self, name: str) -> Persona | None:
        """Get persona by display name.

        Args:
            name: Persona display name (case-insensitive matching)

        Returns:
            Persona if found, None otherwise
        """
        ...

    async def get_by_normalized_name(self, normalized_name: str) -> Persona | None:
        """Get persona by normalized name.

        Args:
            normalized_name: Pre-normalized persona name

        Returns:
            Persona if found, None otherwise
        """
        ...

    async def get_by_docname(self, docname: str) -> list[Persona]:
        """Get all personas defined in a specific document.

        Args:
            docname: RST document name

        Returns:
            List of personas from that document
        """
        ...

    async def clear_by_docname(self, docname: str) -> int:
        """Remove all personas defined in a specific document.

        Used during incremental builds when a document is re-read.

        Args:
            docname: RST document name

        Returns:
            Number of personas removed
        """
        ...
