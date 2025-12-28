"""Memory implementation of PersonaRepository."""

import logging

from julee.core.infrastructure.repositories.memory.base import MemoryRepositoryMixin
from julee.hcd.entities.persona import Persona
from julee.hcd.repositories.persona import PersonaRepository
from julee.hcd.utils import normalize_name

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

    # -------------------------------------------------------------------------
    # BaseRepository implementation (delegating to protected helpers)
    # -------------------------------------------------------------------------

    async def get(self, entity_id: str) -> Persona | None:
        """Get a persona by slug."""
        return self._get_entity(entity_id)

    async def get_many(self, entity_ids: list[str]) -> dict[str, Persona | None]:
        """Get multiple personas by slug."""
        return self._get_many_entities(entity_ids)

    async def save(self, entity: Persona) -> None:
        """Save a persona."""
        self._save_entity(entity)

    async def list_all(self) -> list[Persona]:
        """List all personas."""
        return self._list_all_entities()

    async def delete(self, entity_id: str) -> bool:
        """Delete a persona by slug."""
        return self._delete_entity(entity_id)

    async def clear(self) -> None:
        """Clear all personas."""
        self._clear_storage()

    # -------------------------------------------------------------------------
    # PersonaRepository-specific queries
    # -------------------------------------------------------------------------

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

    async def list_slugs(self) -> set[str]:
        """List all persona slugs."""
        return self._list_slugs()

    async def list_filtered(
        self,
        solution_slug: str | None = None,
    ) -> list[Persona]:
        """List personas matching filters.

        Uses AND logic when multiple filters are provided.
        """
        results = list(self.storage.values())

        # Filter by solution
        if solution_slug is not None:
            results = [p for p in results if p.solution_slug == solution_slug]

        return results
