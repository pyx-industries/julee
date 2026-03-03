"""
PollingResultHandler protocol for cross-bounded-context polling orchestration.

This module defines the PollingResultHandler protocol that enables cross-BC
coordination when new data is detected during polling operations. Following
ADR 003, this handler accepts domain-relevant arguments and allows the
solution provider to decide what happens with newly detected data.

The polling system recognizes the condition (new data detected) and hands off
to the handler without knowing what the handler does - this is the
"green-dotted-egg-handler" principle.

By the time handle_new_data() is called, the NewDataDetectionPipeline has
already translated raw bytes into item IDs via the NewDataAnalyzer. Handlers
therefore work with structured identifiers, not raw content.
"""

from typing import Protocol, runtime_checkable

from julee.core.entities.acknowledgement import Acknowledgement


@runtime_checkable
class PollingResultHandler(Protocol):
    """
    Handler for new data detected during polling operations.

    This protocol enables cross-bounded-context orchestration by allowing
    polling systems to hand off newly detected item IDs to solution-specific
    processing without knowing what that processing entails.

    Handlers may implement any orchestration pattern:
    - Start Temporal workflows
    - Queue messages
    - Trigger use cases directly
    - Log and notify
    - Complex multi-step processing

    The handler receives item IDs (strings) rather than raw bytes because the
    NewDataDetectionPipeline runs a NewDataAnalyzer before calling the handler.
    This keeps use-case logic out of handlers and makes handlers pure dispatchers.
    """

    async def handle_new_data(
        self,
        endpoint_id: str,
        new_item_ids: list[str],
        content_hash: str,
    ) -> Acknowledgement:
        """
        Handle newly detected items from a polling operation.

        This method is called when the polling system detects that data at
        an endpoint has changed and the analyzer has identified the new items.
        The handler decides what to do with the item IDs — whether to start
        processing workflows, queue work, send notifications, or any other
        domain-specific action.

        Args:
            endpoint_id: Unique identifier for the polled endpoint
            new_item_ids: List of item IDs identified as new or changed by the analyzer
            content_hash: SHA256 hash of the new content for deduplication/tracking

        Returns:
            Acknowledgement indicating handler response:
            - wilco: Handler will process the new data
            - unable: Handler cannot process (resource constraints, invalid state, etc.)
            - roger: Handler acknowledges but makes no processing commitment

        Raises:
            Exception: Handlers may raise exceptions for critical failures,
                      but should prefer returning Acknowledgement.unable() with
                      error details to avoid failing the polling workflow.
        """
        ...
