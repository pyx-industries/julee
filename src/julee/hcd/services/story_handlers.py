"""Handler protocols for Story domain conditions.

These protocols define the handoff interface for story-related conditions.
Use cases recognize these conditions and hand off to the appropriate handler.
The handler implementation knows what other actions are required.
"""

from typing import Protocol

from julee.core.entities.acknowledgement import Acknowledgement
from julee.hcd.entities.story import Story


class OrphanStoryHandler(Protocol):
    """Handler for stories created without an epic assignment.

    Called when a story is created/updated and has no epic_slug.
    The handler decides what to do: suggest epics, auto-assign, notify, etc.
    """

    async def handle(self, story: Story) -> Acknowledgement:
        """Handle an orphan story."""
        ...


class UnknownPersonaHandler(Protocol):
    """Handler for stories referencing an unknown persona.

    Called when a story's persona doesn't match any known Persona entity.
    The handler decides what to do: create persona, suggest match, flag for review.
    """

    async def handle(self, story: Story, persona_name: str) -> Acknowledgement:
        """Handle a story with unknown persona."""
        ...


class StoryCreatedHandler(Protocol):
    """Coarse-grained handler for post-creation orchestration.

    Alternative to fine-grained handlers. Called after any story creation.
    The handler inspects the story and decides what orchestration is needed.
    """

    async def handle(self, story: Story) -> Acknowledgement:
        """Handle a newly created story."""
        ...
