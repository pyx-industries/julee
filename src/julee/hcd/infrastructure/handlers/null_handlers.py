"""Null handler implementations for testing and development.

Null handlers acknowledge without action. Used for:
- Testing use cases in isolation
- Development environments
- Default when no handler configured
"""

from julee.core.entities.acknowledgement import Acknowledgement
from julee.hcd.entities.story import Story


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
