"""Sphinx environment implementation of StoryRepository."""

from typing import TYPE_CHECKING

from julee.hcd.entities.story import Story
from julee.hcd.domain.repositories.story import StoryRepository
from julee.hcd.utils import normalize_name

from .base import SphinxEnvRepositoryMixin

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment


class SphinxEnvStoryRepository(SphinxEnvRepositoryMixin[Story], StoryRepository):
    """Sphinx env-backed implementation of StoryRepository.

    Stores stories in env.hcd_storage["stories"] for parallel-safe
    Sphinx builds.
    """

    def __init__(self, env: "BuildEnvironment") -> None:
        """Initialize with Sphinx build environment."""
        self.env = env
        self.entity_name = "Story"
        self.entity_key = "stories"
        self.id_field = "slug"
        self.entity_class = Story

    async def get_by_app(self, app_slug: str) -> list[Story]:
        """Get all stories for an application."""
        app_normalized = normalize_name(app_slug)
        storage = self._get_storage()
        result = []
        for data in storage.values():
            if data.get("app_normalized") == app_normalized:
                result.append(self._deserialize(data))
        return result

    async def get_by_persona(self, persona: str) -> list[Story]:
        """Get all stories for a persona."""
        persona_normalized = normalize_name(persona)
        storage = self._get_storage()
        result = []
        for data in storage.values():
            if data.get("persona_normalized") == persona_normalized:
                result.append(self._deserialize(data))
        return result

    async def get_by_feature_title(self, feature_title: str) -> Story | None:
        """Get a story by its feature title."""
        title_normalized = normalize_name(feature_title)
        storage = self._get_storage()
        for data in storage.values():
            if normalize_name(data.get("feature_title", "")) == title_normalized:
                return self._deserialize(data)
        return None

    async def get_apps_with_stories(self) -> set[str]:
        """Get the set of app slugs that have stories."""
        storage = self._get_storage()
        return {data.get("app_slug") for data in storage.values() if data.get("app_slug")}

    async def get_all_personas(self) -> set[str]:
        """Get all unique personas across all stories."""
        storage = self._get_storage()
        personas = set()
        for data in storage.values():
            persona = data.get("persona_normalized")
            if persona and persona != "unknown":
                personas.add(persona)
        return personas
