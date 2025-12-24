"""NewDataDetectionUseCase for polling with change detection.

This use case handles the business logic of:
1. Polling an endpoint
2. Computing content hash
3. Detecting changes from previous state
4. Returning structured results for routing

The use case is designed to be called from a Pipeline, which handles
the Temporal workflow concerns (durability, routing, dispatch tracking).

See: docs/architecture/proposals/pipeline_router_design.md
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from julee.contrib.polling.domain.use_cases.requests import (
    NewDataDetectionRequest,
    PollEndpointRequest,
)
from julee.contrib.polling.domain.use_cases.responses import NewDataDetectionResponse

if TYPE_CHECKING:
    from julee.contrib.polling.domain.services.poller import PollerService

logger = logging.getLogger(__name__)


class NewDataDetectionUseCase:
    """Detect new data at a polled endpoint.

    This use case:
    1. Polls an endpoint using the provided poller service
    2. Computes a hash of the retrieved content
    3. Compares with previous hash to detect changes
    4. Returns structured results for downstream routing

    Error Handling:
        Polling failures are captured in the response (error field)
        rather than raised as exceptions. This allows the pipeline
        to route to error handling workflows when needed.
    """

    def __init__(self, poller_service: PollerService) -> None:
        """Initialize with dependencies.

        Args:
            poller_service: Service for polling endpoints
        """
        self._poller_service = poller_service

    async def execute(self, request: NewDataDetectionRequest) -> NewDataDetectionResponse:
        """Execute the new data detection.

        Args:
            request: Contains polling config and optional previous hash

        Returns:
            NewDataDetectionResponse with detection results.
            On error, success=False and error field is populated.
        """
        logger.info(
            "Executing new data detection",
            extra={
                "endpoint_id": request.endpoint_identifier,
                "has_previous_hash": request.previous_hash is not None,
            },
        )

        try:
            # Step 1: Poll the endpoint
            poll_request = PollEndpointRequest(
                endpoint_identifier=request.endpoint_identifier,
                polling_protocol=request.polling_protocol,
                connection_params=request.connection_params,
                polling_params=request.polling_params,
                timeout_seconds=request.timeout_seconds,
            )
            polling_result = await self._poller_service.poll_endpoint(poll_request)

            # Step 2: Compute content hash
            content_hash = hashlib.sha256(polling_result.content).hexdigest()

            # Step 3: Detect changes
            is_first_poll = request.previous_hash is None
            has_new_data = not is_first_poll and content_hash != request.previous_hash

            logger.info(
                "New data detection completed",
                extra={
                    "endpoint_id": request.endpoint_identifier,
                    "has_new_data": has_new_data,
                    "is_first_poll": is_first_poll,
                    "content_hash": content_hash[:8] + "...",
                    "previous_hash": (
                        request.previous_hash[:8] + "..."
                        if request.previous_hash
                        else None
                    ),
                },
            )

            return NewDataDetectionResponse(
                success=polling_result.success,
                content=polling_result.content,
                content_hash=content_hash,
                polled_at=polling_result.polled_at,
                endpoint_id=request.endpoint_identifier,
                has_new_data=has_new_data,
                previous_hash=request.previous_hash,
                is_first_poll=is_first_poll,
                error=None,
            )

        except Exception as e:
            logger.error(
                "New data detection failed",
                extra={
                    "endpoint_id": request.endpoint_identifier,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            # Return error response instead of raising
            # This allows the pipeline to route to error handlers
            return NewDataDetectionResponse(
                success=False,
                content=b"",
                content_hash="",
                polled_at=datetime.now(timezone.utc),
                endpoint_id=request.endpoint_identifier,
                has_new_data=False,
                previous_hash=request.previous_hash,
                is_first_poll=request.previous_hash is None,
                error=f"{type(e).__name__}: {e}",
            )
