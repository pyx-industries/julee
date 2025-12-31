"""OperationRecord entity for tracking service operation invocations.

When a use case calls a service method, the invocation can be recorded as an
OperationRecord. This enables supply chain projections like UNTP to map
individual operations to traceability events.

The record captures:
- What service was called (service_type as fully qualified name)
- Which method was invoked
- Timing information
- Summaries of inputs and outputs (for audit, not full data)
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OperationRecord(BaseModel):
    """Immutable record of a service operation invocation.

    Captures the essential information about a service method call
    within a use case execution. Used for:

    - Audit trails (what operations occurred)
    - Supply chain projection (operations → EPCIS events)
    - Performance analysis (timing)
    - Debugging (input/output summaries)

    The service_type is stored as a fully qualified string (e.g.
    "myapp.services.ProcessingService") to enable runtime lookup
    of the service's supply chain semantics without creating
    import dependencies.
    """

    model_config = ConfigDict(frozen=True)

    operation_id: str
    """Unique identifier for this operation invocation."""

    service_type: str
    """Fully qualified name of the service protocol (e.g. 'myapp.services.ProcessingService')."""

    method_name: str
    """Name of the method that was called."""

    started_at: datetime
    """When the operation started."""

    completed_at: datetime
    """When the operation completed."""

    input_summary: dict = Field(default_factory=dict)
    """Serializable summary of inputs (not full data, just metadata)."""

    output_summary: dict = Field(default_factory=dict)
    """Serializable summary of outputs (not full data, just metadata)."""

    metadata: dict = Field(default_factory=dict)
    """Additional context (actor, location, etc.)."""

    @property
    def duration_ms(self) -> int:
        """Duration of the operation in milliseconds."""
        delta = self.completed_at - self.started_at
        return int(delta.total_seconds() * 1000)
