"""
Polling domain models.

This module contains the core domain models for polling operations,
including configuration and result models.
"""

from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from julee.core.entities.entity import Entity


class PollingProtocol(str, Enum):
    """Supported polling protocols."""

    HTTP = "http"


class SchedulingPolicy(str, Enum):
    """Scheduling policy for polling operations."""

    ALLOW_OVERLAP = "allow_overlap"
    SKIP_IF_RUNNING = "skip_if_running"


class PollingConfig(Entity):
    """Configuration for a polling operation."""

    endpoint_identifier: str = Field(description="Unique identifier for this endpoint")
    polling_protocol: PollingProtocol
    connection_params: Mapping[str, Any] = Field(default_factory=dict)
    polling_params: Mapping[str, Any] = Field(default_factory=dict)
    timeout_seconds: int | None = Field(default=30)
    scheduling_policy: SchedulingPolicy = Field(
        default=SchedulingPolicy.ALLOW_OVERLAP,
        description="Policy for handling overlapping polling operations",
    )


class PollingResult(Entity):
    """Result of a polling operation."""

    success: bool
    content: bytes
    metadata: Mapping[str, Any] = Field(default_factory=dict)
    polled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_hash: str | None = None
    error_message: str | None = None

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, v):
        """Convert list of integers to bytes (for Temporal serialization compatibility)."""
        if isinstance(v, list):
            # Temporal may serialize bytes as list of integers
            return bytes(v)
        elif isinstance(v, str):
            # Handle string input
            return v.encode("utf-8")
        elif isinstance(v, bytes):
            return v
        else:
            raise ValueError(
                f"Content must be bytes, string, or list of integers, got {type(v)}"
            )
