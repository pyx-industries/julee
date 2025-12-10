"""
Polling domain models.

This module contains the core domain models for polling operations,
including configuration and result models.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

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
