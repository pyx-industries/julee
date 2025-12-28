"""Null handler implementations for testing and development.

Null handlers acknowledge without action. Used for:
- Testing use cases in isolation
- Development environments
- Default when no handler configured
"""

from julee.core.entities.acknowledgement import Acknowledgement


class NullNewDataHandler:
    """Null handler for new data detection. Acknowledges without action."""

    async def handle(
        self,
        endpoint_id: str,
        content: bytes,
        content_hash: str,
    ) -> Acknowledgement:
        """Accept the data without taking any action."""
        return Acknowledgement.wilco()
