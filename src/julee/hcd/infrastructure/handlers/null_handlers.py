"""Null and logging handler implementations.

Null handlers acknowledge without action. Used for testing.
Logging handlers report conditions to the log. Used for development/production.
"""

import logging

from julee.core.entities.acknowledgement import Acknowledgement
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.journey import Journey
from julee.hcd.entities.story import Story

logger = logging.getLogger(__name__)


# =============================================================================
# Null Handlers - for testing
# =============================================================================


class NullOrphanStoryHandler:
    """Null handler for orphan stories. Acknowledges without action."""

    async def handle(self, story: Story) -> Acknowledgement:
        """Accept the story without taking any action."""
        return Acknowledgement.wilco()


class NullUnknownPersonaHandler:
    """Null handler for unknown personas. Acknowledges without action."""

    async def handle(self, story: Story, persona_name: str) -> Acknowledgement:
        """Accept the story without taking any action."""
        return Acknowledgement.wilco()


class NullStoryCreatedHandler:
    """Null handler for story creation. Acknowledges without action."""

    async def handle(self, story: Story) -> Acknowledgement:
        """Accept the story without taking any action."""
        return Acknowledgement.wilco()


class NullEmptyEpicHandler:
    """Null handler for empty epics. Acknowledges without action."""

    async def handle(self, epic: Epic) -> Acknowledgement:
        """Accept the epic without taking any action."""
        return Acknowledgement.wilco()


class NullUnknownStoryRefHandler:
    """Null handler for unknown story refs. Acknowledges without action."""

    async def handle(self, epic: Epic, unknown_refs: list[str]) -> Acknowledgement:
        """Accept the epic without taking any action."""
        return Acknowledgement.wilco()


class NullEpicCreatedHandler:
    """Null handler for epic creation. Acknowledges without action."""

    async def handle(self, epic: Epic) -> Acknowledgement:
        """Accept the epic without taking any action."""
        return Acknowledgement.wilco()


class NullUnknownJourneyPersonaHandler:
    """Null handler for unknown journey persona. Acknowledges without action."""

    async def handle(self, journey: Journey, persona_name: str) -> Acknowledgement:
        """Accept the journey without taking any action."""
        return Acknowledgement.wilco()


class NullUnknownJourneyStoryRefHandler:
    """Null handler for unknown journey story refs. Acknowledges without action."""

    async def handle(self, journey: Journey, unknown_refs: list[str]) -> Acknowledgement:
        """Accept the journey without taking any action."""
        return Acknowledgement.wilco()


class NullUnknownJourneyEpicRefHandler:
    """Null handler for unknown journey epic refs. Acknowledges without action."""

    async def handle(self, journey: Journey, unknown_refs: list[str]) -> Acknowledgement:
        """Accept the journey without taking any action."""
        return Acknowledgement.wilco()


class NullEmptyJourneyHandler:
    """Null handler for empty journeys. Acknowledges without action."""

    async def handle(self, journey: Journey) -> Acknowledgement:
        """Accept the journey without taking any action."""
        return Acknowledgement.wilco()


class NullJourneyCreatedHandler:
    """Null handler for journey creation. Acknowledges without action."""

    async def handle(self, journey: Journey) -> Acknowledgement:
        """Accept the journey without taking any action."""
        return Acknowledgement.wilco()


# =============================================================================
# Logging Handlers - for development/production
# =============================================================================


class LoggingOrphanStoryHandler:
    """Handler that logs orphan story conditions.

    Fine-grained handler - no internal use case, interacts directly with
    logging infrastructure.
    """

    async def handle(self, story: Story) -> Acknowledgement:
        """Log the orphan story condition."""
        logger.warning(
            "Orphan story detected: not in any epic",
            extra={
                "story_slug": story.slug,
                "feature_title": story.feature_title,
                "app_slug": story.app_slug,
                "persona": story.persona,
            },
        )
        return Acknowledgement.wilco(
            warnings=[f"Story '{story.feature_title}' is not in any epic"],
        )


class LoggingUnknownPersonaHandler:
    """Handler that logs unknown persona conditions.

    Fine-grained handler - no internal use case, interacts directly with
    logging infrastructure.
    """

    async def handle(self, story: Story, persona_name: str) -> Acknowledgement:
        """Log the unknown persona condition."""
        logger.warning(
            "Unknown persona referenced in story",
            extra={
                "story_slug": story.slug,
                "persona_name": persona_name,
                "feature_title": story.feature_title,
            },
        )
        return Acknowledgement.wilco(
            warnings=[f"Persona '{persona_name}' is not defined"],
        )


# -----------------------------------------------------------------------------
# Epic Logging Handlers
# -----------------------------------------------------------------------------


class LoggingEmptyEpicHandler:
    """Handler that logs empty epic conditions.

    Fine-grained handler - no internal use case, interacts directly with
    logging infrastructure.
    """

    async def handle(self, epic: Epic) -> Acknowledgement:
        """Log the empty epic condition."""
        logger.warning(
            "Empty epic detected: no story references",
            extra={
                "epic_slug": epic.slug,
                "description": epic.description,
            },
        )
        return Acknowledgement.wilco(
            warnings=[f"Epic '{epic.slug}' has no stories"],
        )


class LoggingUnknownStoryRefHandler:
    """Handler that logs unknown story ref conditions.

    Fine-grained handler - no internal use case, interacts directly with
    logging infrastructure.
    """

    async def handle(self, epic: Epic, unknown_refs: list[str]) -> Acknowledgement:
        """Log the unknown story refs condition."""
        logger.warning(
            "Unknown story references in epic",
            extra={
                "epic_slug": epic.slug,
                "unknown_refs": unknown_refs,
            },
        )
        refs_str = ", ".join(f"'{r}'" for r in unknown_refs)
        return Acknowledgement.wilco(
            warnings=[f"Epic '{epic.slug}' references unknown stories: {refs_str}"],
        )


# -----------------------------------------------------------------------------
# Journey Logging Handlers
# -----------------------------------------------------------------------------


class LoggingUnknownJourneyPersonaHandler:
    """Handler that logs unknown journey persona conditions.

    Fine-grained handler - no internal use case, interacts directly with
    logging infrastructure.
    """

    async def handle(self, journey: Journey, persona_name: str) -> Acknowledgement:
        """Log the unknown persona condition."""
        logger.warning(
            "Unknown persona referenced in journey",
            extra={
                "journey_slug": journey.slug,
                "persona_name": persona_name,
            },
        )
        return Acknowledgement.wilco(
            warnings=[f"Journey '{journey.slug}' references unknown persona '{persona_name}'"],
        )


class LoggingUnknownJourneyStoryRefHandler:
    """Handler that logs unknown journey story ref conditions.

    Fine-grained handler - no internal use case, interacts directly with
    logging infrastructure.
    """

    async def handle(self, journey: Journey, unknown_refs: list[str]) -> Acknowledgement:
        """Log the unknown story refs condition."""
        logger.warning(
            "Unknown story references in journey",
            extra={
                "journey_slug": journey.slug,
                "unknown_refs": unknown_refs,
            },
        )
        refs_str = ", ".join(f"'{r}'" for r in unknown_refs)
        return Acknowledgement.wilco(
            warnings=[f"Journey '{journey.slug}' references unknown stories: {refs_str}"],
        )


class LoggingUnknownJourneyEpicRefHandler:
    """Handler that logs unknown journey epic ref conditions.

    Fine-grained handler - no internal use case, interacts directly with
    logging infrastructure.
    """

    async def handle(self, journey: Journey, unknown_refs: list[str]) -> Acknowledgement:
        """Log the unknown epic refs condition."""
        logger.warning(
            "Unknown epic references in journey",
            extra={
                "journey_slug": journey.slug,
                "unknown_refs": unknown_refs,
            },
        )
        refs_str = ", ".join(f"'{r}'" for r in unknown_refs)
        return Acknowledgement.wilco(
            warnings=[f"Journey '{journey.slug}' references unknown epics: {refs_str}"],
        )


class LoggingEmptyJourneyHandler:
    """Handler that logs empty journey conditions.

    Fine-grained handler - no internal use case, interacts directly with
    logging infrastructure.
    """

    async def handle(self, journey: Journey) -> Acknowledgement:
        """Log the empty journey condition."""
        logger.warning(
            "Empty journey detected: no steps",
            extra={
                "journey_slug": journey.slug,
                "persona": journey.persona,
            },
        )
        return Acknowledgement.wilco(
            warnings=[f"Journey '{journey.slug}' has no steps"],
        )
