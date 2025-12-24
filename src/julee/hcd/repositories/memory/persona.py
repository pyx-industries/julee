"""Memory implementation of PersonaRepository."""

import logging

from julee.hcd.entities.persona import Persona
from julee.hcd.utils import normalize_name

from ...domain.repositories.persona import PersonaRepository
from .base import MemoryRepositoryMixin

logger = logging.getLogger(__name__)


class MemoryPersonaRepository(MemoryRepositoryMixin[Persona], PersonaRepository):
    """In-memory implementation of PersonaRepository.

    Personas are stored in a dictionary keyed by slug. This implementation
    is used during Sphinx builds where personas are populated during doctree
    processing and support incremental builds via docname tracking.
    """

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.storage: dict[str, Persona] = {}
        self.entity_name = "Persona"
        self.id_field = "slug"

    async def get_by_name(self, name: str) -> Persona | None:
        """Get persona by display name (case-insensitive)."""
        name_normalized = normalize_name(name)
        for persona in self.storage.values():
            if persona.normalized_name == name_normalized:
                return persona
        return None

    async def get_by_normalized_name(self, normalized_name: str) -> Persona | None:
        """Get persona by pre-normalized name."""
        for persona in self.storage.values():
            if persona.normalized_name == normalized_name:
                return persona
        return None

    async def get_by_docname(self, docname: str) -> list[Persona]:
        """Get all personas defined in a specific document."""
        return [
            persona for persona in self.storage.values() if persona.docname == docname
        ]

    async def clear_by_docname(self, docname: str) -> int:
        """Remove all personas defined in a specific document."""
        to_remove = [
            slug for slug, persona in self.storage.items() if persona.docname == docname
        ]
        for slug in to_remove:
            del self.storage[slug]
        return len(to_remove)
