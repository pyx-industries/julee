"""Sphinx environment implementation of JourneyRepository."""

from typing import TYPE_CHECKING

from julee.hcd.entities.journey import Journey
from julee.hcd.domain.repositories.journey import JourneyRepository
from julee.hcd.utils import normalize_name

from .base import SphinxEnvRepositoryMixin

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment


class SphinxEnvJourneyRepository(SphinxEnvRepositoryMixin[Journey], JourneyRepository):
    """Sphinx env-backed implementation of JourneyRepository.

    Stores journeys in env.hcd_storage["journeys"] for parallel-safe
    Sphinx builds.
    """

    def __init__(self, env: "BuildEnvironment") -> None:
        """Initialize with Sphinx build environment."""
        self.env = env
        self.entity_name = "Journey"
        self.entity_key = "journeys"
        self.id_field = "slug"
        self.entity_class = Journey

    async def get_by_persona(self, persona: str) -> list[Journey]:
        """Get all journeys for a persona."""
        persona_normalized = normalize_name(persona)
        storage = self._get_storage()
        result = []
        for data in storage.values():
            if data.get("persona_normalized") == persona_normalized:
                result.append(self._deserialize(data))
        return result

    async def get_by_docname(self, docname: str) -> list[Journey]:
        """Get all journeys defined in a specific document."""
        return await self.find_by_docname(docname)

    async def get_dependents(self, journey_slug: str) -> list[Journey]:
        """Get journeys that depend on a specific journey."""
        storage = self._get_storage()
        result = []
        for data in storage.values():
            entity = self._deserialize(data)
            if entity.has_dependency(journey_slug):
                result.append(entity)
        return result

    async def get_dependencies(self, journey_slug: str) -> list[Journey]:
        """Get journeys that a specific journey depends on."""
        storage = self._get_storage()
        journey_data = storage.get(journey_slug)
        if not journey_data:
            return []
        depends_on = journey_data.get("depends_on", [])
        result = []
        for dep_slug in depends_on:
            dep_data = storage.get(dep_slug)
            if dep_data:
                result.append(self._deserialize(dep_data))
        return result

    async def get_all_personas(self) -> set[str]:
        """Get all unique personas across all journeys."""
        storage = self._get_storage()
        personas = set()
        for data in storage.values():
            persona = data.get("persona_normalized")
            if persona:
                personas.add(persona)
        return personas

    async def get_with_story_ref(self, story_title: str) -> list[Journey]:
        """Get journeys that reference a specific story."""
        story_normalized = normalize_name(story_title)
        storage = self._get_storage()
        result = []
        for data in storage.values():
            entity = self._deserialize(data)
            if any(
                normalize_name(ref) == story_normalized
                for ref in entity.get_story_refs()
            ):
                result.append(entity)
        return result

    async def get_with_epic_ref(self, epic_slug: str) -> list[Journey]:
        """Get journeys that reference a specific epic."""
        storage = self._get_storage()
        result = []
        for data in storage.values():
            entity = self._deserialize(data)
            if epic_slug in entity.get_epic_refs():
                result.append(entity)
        return result
