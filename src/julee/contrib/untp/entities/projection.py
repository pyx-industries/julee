"""Projection mapping entities for UNTP.

Defines how operation records are mapped to UNTP events based on
the supply chain operation type of the service that was invoked.
"""

from pydantic import BaseModel, ConfigDict, Field


class ProjectionMapping(BaseModel):
    """Configuration for how operations are projected to UNTP events.

    This entity can be used to customize projection behavior for
    specific service types or bounded contexts.
    """

    model_config = ConfigDict(frozen=True)

    mapping_id: str = Field(
        ...,
        description="Unique identifier for this mapping",
    )
    service_type_pattern: str = Field(
        ...,
        description="Glob pattern matching service types (e.g., 'myapp.services.*')",
    )
    event_type_override: str | None = Field(
        default=None,
        description="Override the inferred event type",
    )
    include_in_projection: bool = Field(
        default=True,
        description="Whether to include matching operations in projection",
    )
    metadata_extractors: dict[str, str] = Field(
        default_factory=dict,
        description="JSONPath expressions to extract event metadata from operation",
    )


class ProjectionResult(BaseModel):
    """Result of projecting an operation to UNTP events.

    Contains the projected event along with metadata about the projection.
    """

    model_config = ConfigDict(frozen=True)

    operation_id: str = Field(
        ...,
        description="ID of the source OperationRecord",
    )
    event_id: str = Field(
        ...,
        description="ID of the projected event",
    )
    event_type: str = Field(
        ...,
        description="Type of the projected event",
    )
    supply_chain_operation_type: str | None = Field(
        default=None,
        description="The supply chain operation type from the service decorator",
    )
    mapping_id: str | None = Field(
        default=None,
        description="ID of the ProjectionMapping used, if any",
    )
    skipped: bool = Field(
        default=False,
        description="Whether the operation was skipped (no projection)",
    )
    skip_reason: str | None = Field(
        default=None,
        description="Reason for skipping projection",
    )
