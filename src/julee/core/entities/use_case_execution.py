"""UseCaseExecution entity for recording use case invocations.

A UseCaseExecution is an immutable record of a use case being executed.
It captures:
- The use case identity (name, bounded context)
- Timing information
- Request/response summaries
- Operations performed (service calls)
- Optional context (actor, pipeline)

This entity is the primary input for supply chain projections.
UNTP's DigitalTraceabilityEvent is projected from the operation_records
within a UseCaseExecution.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from julee.core.entities.operation_record import OperationRecord


class UseCaseExecution(BaseModel):
    """Immutable record of a use case execution.

    Captures everything needed to understand what happened during
    a use case invocation, without storing full request/response data.

    The operation_records list contains records of each service method
    call made during execution. This enables fine-grained traceability:
    a single use case execution may produce multiple UNTP events,
    one per operation.

    Use cases:
    - Audit trails (what use cases ran, when, with what results)
    - Supply chain projection (execution → UNTP credentials)
    - Performance monitoring (duration, operation counts)
    - Debugging (trace through operations)
    """

    model_config = ConfigDict(frozen=True)

    execution_id: str
    """Unique identifier for this execution."""

    use_case_name: str
    """Name of the use case that was executed."""

    bounded_context: str
    """Bounded context containing the use case."""

    started_at: datetime
    """When execution started."""

    completed_at: datetime
    """When execution completed."""

    duration_ms: int
    """Total duration in milliseconds."""

    request_summary: dict = Field(default_factory=dict)
    """Serializable summary of the request (not full data)."""

    response_summary: dict = Field(default_factory=dict)
    """Serializable summary of the response (not full data)."""

    operation_records: list[OperationRecord] = Field(default_factory=list)
    """Records of service operations invoked during execution."""

    actor_id: str | None = None
    """Optional identifier of the actor who triggered execution."""

    pipeline_id: str | None = None
    """Optional identifier of the pipeline if run as workflow."""

    @property
    def operation_count(self) -> int:
        """Number of service operations performed."""
        return len(self.operation_records)

    @property
    def service_types_used(self) -> set[str]:
        """Set of service types that were invoked."""
        return {op.service_type for op in self.operation_records}
