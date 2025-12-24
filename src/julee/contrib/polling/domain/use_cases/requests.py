"""Request DTOs for polling use cases.

Following clean architecture principles, request models define the contract
between use cases and their callers.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..models.polling_config import PollingConfig, PollingProtocol


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
        default=None,
        description="Hash from previous poll (None if first run)"
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
