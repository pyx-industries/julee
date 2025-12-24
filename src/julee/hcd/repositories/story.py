"""StoryRepository protocol.

Defines the interface for story data access.
"""

from typing import Protocol, runtime_checkable

from julee.core.repositories.base import BaseRepository
from julee.hcd.entities.story import Story


@runtime_checkable
class StoryRepository(BaseRepository[Story], Protocol):
    """Repository protocol for Story entities.

    Extends BaseRepository with story-specific query methods.
    Stories are indexed from .feature files and are read-only during
    a Sphinx build (populated at builder-inited, queried during rendering).
    """

    async def get_by_app(self, app_slug: str) -> list[Story]:
        """Get all stories for an application.

        Args:
            app_slug: Application slug (e.g., "staff-portal")

        Returns:
            List of stories belonging to the app
        """
        ...

    async def get_by_persona(self, persona: str) -> list[Story]:
        """Get all stories for a persona.

        Args:
            persona: Persona name (case-insensitive matching)

        Returns:
            List of stories where the persona matches
        """
        ...

    async def get_by_feature_title(self, feature_title: str) -> Story | None:
        """Get a story by its feature title.

        Args:
            feature_title: The Feature: line content (case-insensitive)

        Returns:
            Story if found, None otherwise
        """
        ...

    async def get_apps_with_stories(self) -> set[str]:
        """Get the set of app slugs that have stories.

        Returns:
            Set of app slugs (normalized)
        """
        ...

    async def get_all_personas(self) -> set[str]:
        """Get all unique personas across all stories.

        Returns:
            Set of persona names (normalized)
        """
        ...
