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
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from julee.contrib.polling.entities.polling_config import (
    PollingConfig,
    PollingProtocol,
)

if TYPE_CHECKING:
    from julee.contrib.polling.services.poller import PollerService

logger = logging.getLogger(__name__)


# =============================================================================
# Request Models
# =============================================================================


class PollEndpointRequest(BaseModel):
    """Request for polling an endpoint.

    Contains all parameters needed to configure a polling operation.
    """

    endpoint_identifier: str = Field(description="Unique identifier for this endpoint")
    polling_protocol: PollingProtocol = Field(description="Protocol to use for polling")
    connection_params: dict[str, Any] = Field(
        default_factory=dict, description="Protocol-specific connection parameters"
    )
    polling_params: dict[str, Any] = Field(
        default_factory=dict, description="Protocol-specific polling parameters"
    )
    timeout_seconds: int | None = Field(
        default=30, description="Timeout for the polling operation"
    )

    def to_domain_model(self) -> PollingConfig:
        """Convert to PollingConfig domain model."""
        return PollingConfig(
            endpoint_identifier=self.endpoint_identifier,
            polling_protocol=self.polling_protocol,
            connection_params=self.connection_params,
            polling_params=self.polling_params,
            timeout_seconds=self.timeout_seconds,
        )


class NewDataDetectionRequest(BaseModel):
    """Request for new data detection.

    Contains polling configuration and optional previous state for
    change detection.
    """

    # Polling configuration
    endpoint_identifier: str = Field(description="Unique identifier for this endpoint")
    polling_protocol: PollingProtocol = Field(description="Protocol to use for polling")
    connection_params: dict[str, Any] = Field(
        default_factory=dict, description="Protocol-specific connection parameters"
    )
    polling_params: dict[str, Any] = Field(
        default_factory=dict, description="Protocol-specific polling parameters"
    )
    timeout_seconds: int | None = Field(
        default=30, description="Timeout for the polling operation"
    )

    # Previous state for change detection
    previous_hash: str | None = Field(
        default=None, description="Hash from previous poll (None if first run)"
    )

    def to_polling_config(self) -> PollingConfig:
        """Convert to PollingConfig domain model."""
        return PollingConfig(
            endpoint_identifier=self.endpoint_identifier,
            polling_protocol=self.polling_protocol,
            connection_params=self.connection_params,
            polling_params=self.polling_params,
            timeout_seconds=self.timeout_seconds,
        )


# =============================================================================
# Response Models
# =============================================================================


class PollEndpointResponse(BaseModel):
    """Response from polling an endpoint.

    Contains the raw polling result without any change detection.
    """

    success: bool = Field(description="Whether the poll operation succeeded")
    content: bytes = Field(description="Content retrieved from the endpoint")
    content_hash: str = Field(description="SHA256 hash of the content")
    polled_at: datetime = Field(description="When the polling occurred")


class NewDataDetectionResponse(BaseModel):
    """Response from the new data detection use case.

    Contains detection results that can be used for routing decisions.
    The computed properties `should_process` and `has_error` are designed
    for use in routing conditions.
    """

    # Polling results
    success: bool = Field(description="Whether polling succeeded")
    content: bytes = Field(description="Retrieved content")
    content_hash: str = Field(description="SHA256 hash of current content")
    polled_at: datetime = Field(description="When polling occurred")
    endpoint_id: str = Field(description="Identifier of the polled endpoint")

    # Change detection results
    has_new_data: bool = Field(
        description="Whether new data was detected (hash changed)"
    )
    previous_hash: str | None = Field(
        default=None, description="Hash from previous poll (None if first run)"
    )
    is_first_poll: bool = Field(
        default=False, description="Whether this is the first poll (no previous data)"
    )

    # Error handling
    error: str | None = Field(
        default=None, description="Error message if polling failed"
    )

    # Dispatch tracking (populated by pipeline after routing)
    dispatches: list = Field(
        default_factory=list,
        description="List of PipelineDispatchItem records from run_next()",
    )

    @property
    def should_process(self) -> bool:
        """Whether downstream processing should be triggered.

        Convenience property for routing conditions. Returns True when:
        - Polling succeeded AND new data was detected AND it's not the first poll

        Note: First poll doesn't trigger processing because there's no
        previous data to compare against for meaningful processing.
        """
        return self.success and self.has_new_data and not self.is_first_poll

    @property
    def has_error(self) -> bool:
        """Whether an error occurred during polling.

        Convenience property for routing conditions.
        """
        return self.error is not None or not self.success


# =============================================================================
# UseCase
# =============================================================================


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

    async def execute(
        self, request: NewDataDetectionRequest
    ) -> NewDataDetectionResponse:
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
