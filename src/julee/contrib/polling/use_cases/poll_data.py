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
from julee.contrib.polling.domain.services.new_data_analyzer import NewDataAnalyzer
from julee.contrib.polling.domain.services.poller import PollerService
from julee.contrib.polling.domain.services.polling_result_handler import (
    PollingResultHandler,
)

logger = logging.getLogger(__name__)


class PollDataRequest(BaseModel):
    """Input for PollDataUseCase."""

    config: PollingConfig
    previous_completion: dict | None = None


class PollDataResponse(BaseModel):
    """Output for PollDataUseCase."""

    endpoint_id: str
    content_hash: str
    content: str
    polled_at: str
    new_items_found: bool
    items_processed: int


class PollDataUseCase:
    """
    Use case for polling an endpoint and detecting new data.

    Responsibilities:
    1. Poll the endpoint via the injected PollerService
    2. Compute the SHA-256 hash of the response content
    3. Compare with the previous run's hash (from previous_completion)
    4. If content has changed and an analyzer is set, identify new item IDs
    5. Delegate to the optional PollingResultHandler with the item IDs
    6. Return a PollDataResponse; the pipeline builds the Temporal
       last-completion-result dict from it.

    """

    def __init__(
        self,
        poller: PollerService,
        handler: PollingResultHandler,
        analyzer: NewDataAnalyzer,
    ) -> None:
        self._poller = poller
        self._handler = handler
        self._analyzer = analyzer

    async def execute(self, request: PollDataRequest) -> PollDataResponse:
        """
        Execute the poll-and-detect use case.

        Args:
            request: PollDataRequest containing polling config and
                     the previous run's completion result (may be None
                     for the first run).

        Returns:
            PollDataResponse with polling outcome and detection results.
        """
        config = request.config
        endpoint_id = config.endpoint_identifier

        # Step 1: Poll the endpoint
        polling_result = await self._poller.poll_endpoint(config)
        polled_at = polling_result.polled_at.isoformat()

        # Step 2: Hash current content
        current_content = polling_result.content
        current_hash = hashlib.sha256(current_content).hexdigest()

        # Step 3: Extract previous hash and content
        previous_hash: str | None = None
        previous_data: bytes | None = None
        if (
            request.previous_completion
            and "polling_result" in request.previous_completion
        ):
            previous_hash = request.previous_completion["polling_result"].get(
                "content_hash"
            )
            prev_content_str = request.previous_completion["polling_result"].get(
                "content"
            )
            if prev_content_str:
                previous_data = prev_content_str.encode("utf-8")

        # Step 4: Detect change
        has_new_data = previous_hash != current_hash

        # Step 5: Analyze and invoke handler if new data detected
        items_processed = 0
        if has_new_data:
            try:
                item_ids = await self._analyzer.identify_new_items(
                    previous_data, current_content
                )
                items_processed = len(item_ids)
                await self._handler.handle_new_data(
                    endpoint_id,
                    item_ids,
                    current_hash,
                )
            except Exception as e:
                logger.error(
                    "Analyzer or handler raised an exception; continuing without ack",
                    extra={
                        "endpoint_id": endpoint_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )

        # Step 6: Return completion result
        return PollDataResponse(
            endpoint_id=endpoint_id,
            content_hash=current_hash,
            content=current_content.decode("utf-8", errors="ignore"),
            polled_at=polled_at,
            new_items_found=has_new_data,
            items_processed=items_processed,
        )
