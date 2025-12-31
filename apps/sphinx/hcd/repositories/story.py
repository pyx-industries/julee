"""Sphinx environment implementation of StoryRepository."""

from julee.hcd.entities.story import Story
from julee.hcd.repositories.story import StoryRepository
from julee.hcd.utils import normalize_name

from .base import SphinxEnvRepositoryMixin


class SphinxEnvStoryRepository(SphinxEnvRepositoryMixin[Story], StoryRepository):
    """Sphinx env-backed implementation of StoryRepository.

    Stores stories in env.hcd_storage["stories"] for parallel-safe
    Sphinx builds.
    """

    entity_class = Story

    async def list_filtered(
        self,
        solution_slug: str | None = None,
        app_slug: str | None = None,
        persona: str | None = None,
    ) -> list[Story]:
        """List stories matching filters."""
        stories = await self.list_all()
        if solution_slug is not None:
            stories = [s for s in stories if s.solution_slug == solution_slug]
        if app_slug is not None:
            app_normalized = normalize_name(app_slug)
            stories = [s for s in stories if s.app_normalized == app_normalized]
        if persona is not None:
            persona_normalized = normalize_name(persona)
            stories = [s for s in stories if s.persona_normalized == persona_normalized]
        return stories

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
