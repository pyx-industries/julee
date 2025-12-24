"""JourneyRepository protocol.

Defines the interface for journey data access.
"""

from typing import Protocol, runtime_checkable

from julee.core.repositories.base import BaseRepository
from julee.hcd.entities.journey import Journey


@runtime_checkable
class JourneyRepository(BaseRepository[Journey], Protocol):
    """Repository protocol for Journey entities.

    Extends BaseRepository with journey-specific query methods.
    Journeys are defined in RST documents and support incremental builds
    via docname tracking.
    """

    async def get_by_persona(self, persona: str) -> list[Journey]:
        """Get all journeys for a persona.

        Args:
            persona: Persona name (case-insensitive matching)

        Returns:
            List of journeys where the persona matches
        """
        ...

    async def get_by_docname(self, docname: str) -> list[Journey]:
        """Get all journeys defined in a specific document.

        Args:
            docname: RST document name

        Returns:
            List of journeys from that document
        """
        ...

    async def clear_by_docname(self, docname: str) -> int:
        """Remove all journeys defined in a specific document.

        Used during incremental builds when a document is re-read.

        Args:
            docname: RST document name

        Returns:
            Number of journeys removed
        """
        ...

    async def get_dependents(self, journey_slug: str) -> list[Journey]:
        """Get journeys that depend on a specific journey.

        Args:
            journey_slug: Slug of the journey to find dependents of

        Returns:
            List of journeys that have this journey in depends_on
        """
        ...

    async def get_dependencies(self, journey_slug: str) -> list[Journey]:
        """Get journeys that a specific journey depends on.

        Args:
            journey_slug: Slug of the journey to find dependencies of

        Returns:
            List of journeys that this journey depends on
        """
        ...

    async def get_all_personas(self) -> set[str]:
        """Get all unique personas across all journeys.

        Returns:
            Set of persona names (normalized)
        """
        ...

    async def get_with_story_ref(self, story_title: str) -> list[Journey]:
        """Get journeys that reference a specific story.

        Args:
            story_title: Story feature title (case-insensitive)

        Returns:
            List of journeys containing this story in steps
        """
        ...

    async def get_with_epic_ref(self, epic_slug: str) -> list[Journey]:
        """Get journeys that reference a specific epic.

        Args:
            epic_slug: Epic slug

        Returns:
            List of journeys containing this epic in steps
        """
        ...
