"""Null and logging handler implementations.

Null handlers acknowledge without action. Used for testing.
Logging handlers report conditions to the log. Used for development/production.
"""

import logging

from julee.core.entities.acknowledgement import Acknowledgement
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
