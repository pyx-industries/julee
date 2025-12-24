"""Sphinx environment implementation of PersonaRepository."""

from typing import TYPE_CHECKING

from julee.hcd.domain.models.persona import Persona
from julee.hcd.domain.repositories.persona import PersonaRepository
from julee.hcd.utils import normalize_name

from .base import SphinxEnvRepositoryMixin

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment


class SphinxEnvPersonaRepository(SphinxEnvRepositoryMixin[Persona], PersonaRepository):
    """Sphinx env-backed implementation of PersonaRepository.

    Stores personas in env.hcd_storage["personas"] for parallel-safe
    Sphinx builds.
    """

    def __init__(self, env: "BuildEnvironment") -> None:
        """Initialize with Sphinx build environment."""
        self.env = env
        self.entity_name = "Persona"
        self.entity_key = "personas"
        self.id_field = "slug"
        self.entity_class = Persona

    async def get_by_name(self, name: str) -> Persona | None:
        """Get persona by display name (case-insensitive)."""
        name_normalized = normalize_name(name)
        storage = self._get_storage()
        for data in storage.values():
            if data.get("normalized_name") == name_normalized:
                return self._deserialize(data)
        return None

    async def get_by_normalized_name(self, normalized_name: str) -> Persona | None:
        """Get persona by pre-normalized name."""
        storage = self._get_storage()
        for data in storage.values():
            if data.get("normalized_name") == normalized_name:
                return self._deserialize(data)
        return None

    async def get_by_docname(self, docname: str) -> list[Persona]:
        """Get all personas defined in a specific document."""
        return await self.find_by_docname(docname)
