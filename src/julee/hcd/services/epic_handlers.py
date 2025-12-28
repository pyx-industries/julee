"""Handler protocols for Epic domain conditions.

These protocols define the handoff interface for epic-related conditions.
Use cases recognize these conditions and hand off to the appropriate handler.
"""

from typing import Protocol

from julee.core.entities.acknowledgement import Acknowledgement
from julee.hcd.entities.epic import Epic


class EmptyEpicHandler(Protocol):
    """Handler for epics created without any stories.

    Called when an epic is created/updated and has no story_refs.
    The handler decides what to do: warn, suggest stories, etc.
    """

    async def handle(self, epic: Epic) -> Acknowledgement:
        """Handle an empty epic."""
        ...


class UnknownStoryRefHandler(Protocol):
    """Handler for epics referencing unknown stories.

    Called when an epic's story_refs contains titles not found in StoryRepository.
    The handler decides what to do: warn, suggest corrections, etc.
    """

    async def handle(self, epic: Epic, unknown_refs: list[str]) -> Acknowledgement:
        """Handle an epic with unknown story references."""
        ...


class EpicCreatedHandler(Protocol):
    """Coarse-grained handler for post-creation orchestration.

    Alternative to fine-grained handlers. Called after any epic creation/update.
    The handler inspects the epic and decides what orchestration is needed.
    """

    async def handle(self, epic: Epic) -> Acknowledgement:
        """Handle a newly created/updated epic."""
        ...
