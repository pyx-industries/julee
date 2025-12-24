"""Response DTOs for polling use cases.

Following clean architecture principles, response models define what
use cases return to their callers.
"""

from datetime import datetime

from pydantic import BaseModel, Field


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
        default=None,
        description="Hash from previous poll (None if first run)"
    )
    is_first_poll: bool = Field(
        default=False,
        description="Whether this is the first poll (no previous data)"
    )

    # Error handling
    error: str | None = Field(
        default=None,
        description="Error message if polling failed"
    )

    # Dispatch tracking (populated by pipeline after routing)
    dispatches: list = Field(
        default_factory=list,
        description="List of PipelineDispatchItem records from run_next()"
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
