"""Handler protocols for Journey domain conditions.

These protocols define the handoff interface for journey-related conditions.
Use cases recognize these conditions and hand off to the appropriate handler.
"""

from typing import Protocol

from julee.core.entities.acknowledgement import Acknowledgement
from julee.hcd.entities.journey import Journey


class UnknownJourneyPersonaHandler(Protocol):
    """Handler for journeys referencing an unknown persona.

    Called when a journey's persona doesn't match any known Persona entity.
    The handler decides what to do: create persona, suggest match, flag for review.
    """

    async def handle(self, journey: Journey, persona_name: str) -> Acknowledgement:
        """Handle a journey with unknown persona."""
        ...


class UnknownJourneyStoryRefHandler(Protocol):
    """Handler for journeys referencing unknown stories.

    Called when a journey's story steps reference titles not found in StoryRepository.
    The handler decides what to do: warn, suggest corrections, etc.
    """

    async def handle(
        self, journey: Journey, unknown_refs: list[str]
    ) -> Acknowledgement:
        """Handle a journey with unknown story references."""
        ...


class UnknownJourneyEpicRefHandler(Protocol):
    """Handler for journeys referencing unknown epics.

    Called when a journey's epic steps reference slugs not found in EpicRepository.
    The handler decides what to do: warn, suggest corrections, etc.
    """

    async def handle(
        self, journey: Journey, unknown_refs: list[str]
    ) -> Acknowledgement:
        """Handle a journey with unknown epic references."""
        ...


class EmptyJourneyHandler(Protocol):
    """Handler for journeys created without any steps.

    Called when a journey is created/updated and has no steps.
    The handler decides what to do: warn, suggest steps, etc.
    """

    async def handle(self, journey: Journey) -> Acknowledgement:
        """Handle an empty journey."""
        ...


class JourneyCreatedHandler(Protocol):
    """Coarse-grained handler for post-creation orchestration.

    Alternative to fine-grained handlers. Called after any journey creation/update.
    The handler inspects the journey and decides what orchestration is needed.
    """

    async def handle(self, journey: Journey) -> Acknowledgement:
        """Handle a newly created/updated journey."""
        ...
