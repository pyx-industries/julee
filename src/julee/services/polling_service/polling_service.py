"""
PollingService protocol for external endpoint polling operations.

This module defines the PollingService protocol that handles interactions
with various types of external endpoints for data polling and change detection.

Concrete implementations of this protocol are provided for different polling
mechanisms and are created via factory functions.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class PollingProtocol(str, Enum):
    """Supported polling protocols."""

    HTTP = "http"


class PollingConfig(BaseModel):
    """Configuration for a polling operation."""

    endpoint_identifier: str = Field(description="Unique identifier for this endpoint")
    polling_protocol: PollingProtocol
    connection_params: dict[str, Any] = Field(default_factory=dict)
    polling_params: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int | None = Field(default=30)


class PollingResult(BaseModel):
    """Result of a polling operation."""

    success: bool
    content: bytes
    metadata: dict[str, Any] = Field(default_factory=dict)
    polled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_hash: str | None = None
    error_message: str | None = None


@runtime_checkable
class PollingService(Protocol):
    """
    Protocol for polling external endpoints for data.

    This protocol defines the interface for polling operations across different
    endpoint types. Implementations handle the specifics of different polling
    mechanisms.
    """

    async def poll_endpoint(self, config: PollingConfig) -> PollingResult:
        """
        Poll an endpoint according to the provided configuration.

        Args:
            config: PollingConfig containing endpoint details and parameters

        Returns:
            PollingResult containing the polled data and metadata

        .. rubric:: Implementation Notes

        - Must be idempotent: multiple calls with same config should be safe
        - Should handle endpoint unavailability gracefully
        - Must populate content_hash for change detection
        - Should include relevant metadata for debugging and auditing
        - Must respect timeout and retry configuration

        .. rubric:: Workflow Context

        In Temporal workflows, this method is implemented as an activity
        to ensure polling results are durably stored and consistent
        across workflow replays.
        """
        ...
