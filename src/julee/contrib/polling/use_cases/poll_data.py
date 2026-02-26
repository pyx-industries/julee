"""
PollDataUseCase — generic polling and new-data detection.

This module contains the pure business logic for polling an endpoint
and detecting whether its content has changed since the last run.
It has no knowledge of Temporal, workflows, or application infrastructure.
"""

import hashlib
import logging

from pydantic import BaseModel

from julee.contrib.polling.domain.models.polling_config import PollingConfig
from julee.contrib.polling.domain.services.poller import PollerService
from julee.contrib.polling.domain.services.polling_result_handler import (
    PollingResultHandler,
)

logger = logging.getLogger(__name__)


class PollDataRequest(BaseModel):
    """Input for PollDataUseCase."""

    config: PollingConfig
    previous_completion: dict | None = None


class PollDataUseCase:
    """
    Use case for polling an endpoint and detecting new data.

    Responsibilities:
    1. Poll the endpoint via the injected PollerService
    2. Compute the SHA-256 hash of the response content
    3. Compare with the previous run's hash (from previous_completion)
    4. If content has changed, delegate to the optional PollingResultHandler
    5. Return a completion result dict in the same shape that
       NewDataDetectionPipeline returns, so Temporal schedule
       last-completion-result works unchanged.
    """

    def __init__(
        self,
        poller: PollerService,
        handler: PollingResultHandler | None = None,
    ) -> None:
        self._poller = poller
        self._handler = handler

    async def execute(self, request: PollDataRequest) -> dict:
        """
        Execute the poll-and-detect use case.

        Args:
            request: PollDataRequest containing polling config and
                     the previous run's completion result (may be None
                     for the first run).

        Returns:
            Completion result dict with keys:
              polling_result, detection_result, handler_acknowledgement,
              endpoint_id
        """
        config = request.config
        endpoint_id = config.endpoint_identifier

        # Step 1: Poll the endpoint
        polling_result = await self._poller.poll_endpoint(config)
        polled_at = polling_result.polled_at.isoformat()

        # Step 2: Hash current content
        current_content = polling_result.content
        current_hash = hashlib.sha256(current_content).hexdigest()

        # Step 3: Extract previous hash
        previous_hash: str | None = None
        if request.previous_completion and "polling_result" in request.previous_completion:
            previous_hash = request.previous_completion["polling_result"].get(
                "content_hash"
            )

        # Step 4: Detect change
        has_new_data = previous_hash != current_hash

        # Step 5: Invoke handler if new data detected
        handler_acknowledgement = None
        if has_new_data and self._handler is not None:
            previous_data: bytes | None = None
            if request.previous_completion and "polling_result" in request.previous_completion:
                prev_content_str = request.previous_completion["polling_result"].get(
                    "content"
                )
                if prev_content_str:
                    previous_data = prev_content_str.encode("utf-8")

            try:
                handler_acknowledgement = await self._handler.handle_new_data(
                    endpoint_id,
                    previous_data,
                    current_content,
                    current_hash,
                )
            except Exception as e:
                logger.error(
                    "Handler raised an exception; continuing without ack",
                    extra={
                        "endpoint_id": endpoint_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )
                # handler_acknowledgement stays None to signal the exception

        # Step 6: Return completion result
        return {
            "polling_result": {
                "success": polling_result.success,
                "content_hash": current_hash,
                "content": current_content.decode("utf-8", errors="ignore"),
                "polled_at": polled_at,
                "content_length": len(current_content),
            },
            "detection_result": {
                "has_new_data": has_new_data,
                "previous_hash": previous_hash,
                "current_hash": current_hash,
            },
            "handler_acknowledgement": handler_acknowledgement,
            "endpoint_id": endpoint_id,
        }
