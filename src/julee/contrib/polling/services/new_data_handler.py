"""Handler protocol for newly detected data.

Defines the handoff interface for when polling detects new data.
The use case recognizes the condition (new data detected) and hands off
to the handler. What happens after is the handler's business.
"""

from typing import Protocol

from julee.core.entities.acknowledgement import Acknowledgement


class NewDataHandler(Protocol):
    """Handler for newly detected data from polling.

    Called when NewDataDetectionUseCase detects new data (should_process=True).
    The handler decides what to do: capture document, trigger workflow, etc.

    Solution providers implement this to bridge polling to their specific
    processing needs (e.g., CEAP document capture).
    """

    async def handle(
        self,
        endpoint_id: str,
        content: bytes,
        content_hash: str,
    ) -> Acknowledgement:
        """Handle newly detected data.

        Args:
            endpoint_id: Identifier of the polled endpoint
            content: The new content that was detected
            content_hash: SHA256 hash of the content

        Returns:
            Acknowledgement indicating whether the handler will process the data.
        """
        ...
