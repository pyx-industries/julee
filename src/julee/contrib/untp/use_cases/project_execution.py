"""ProjectExecutionUseCase - project UseCaseExecution to UNTP events.

Maps each OperationRecord within a UseCaseExecution to the appropriate
UNTP traceability event based on the supply chain operation type of
the service that was invoked.

One use case execution can produce multiple UNTP events (one per operation).
"""

import importlib
from datetime import datetime, timezone

from pydantic import BaseModel

from julee.core.decorators import use_case
from julee.core.entities.operation_record import OperationRecord
from julee.core.entities.use_case_execution import UseCaseExecution
from julee.supply_chain.decorators import (
    SupplyChainOperationType,
    get_supply_chain_operation_type,
)

from julee.contrib.untp.entities.event import (
    AggregationEvent,
    EventAction,
    ObjectEvent,
    TransactionEvent,
    TransformationEvent,
)
from julee.contrib.untp.entities.projection import ProjectionResult


class ProjectExecutionRequest(BaseModel):
    """Request to project a use case execution to UNTP events."""

    execution: UseCaseExecution


class ProjectExecutionResponse(BaseModel):
    """Response containing projected UNTP events."""

    events: list[TransformationEvent | TransactionEvent | ObjectEvent | AggregationEvent]
    projection_results: list[ProjectionResult]
    execution_id: str
    event_count: int


def _import_class(fully_qualified_name: str) -> type | None:
    """Import a class from its fully qualified name.

    Args:
        fully_qualified_name: e.g. "myapp.services.ProcessingService"

    Returns:
        The class, or None if import fails
    """
    try:
        parts = fully_qualified_name.rsplit(".", 1)
        if len(parts) != 2:
            return None
        module_path, class_name = parts
        module = importlib.import_module(module_path)
        return getattr(module, class_name, None)
    except (ImportError, AttributeError):
        return None


def _project_operation(
    operation: OperationRecord,
) -> tuple[
    TransformationEvent | TransactionEvent | ObjectEvent | AggregationEvent | None,
    ProjectionResult,
]:
    """Project a single operation to a UNTP event.

    Args:
        operation: The operation record to project

    Returns:
        Tuple of (event or None, projection result)
    """
    # Look up the service class
    service_class = _import_class(operation.service_type)

    if service_class is None:
        return None, ProjectionResult(
            operation_id=operation.operation_id,
            event_id="",
            event_type="",
            skipped=True,
            skip_reason=f"Could not import service class: {operation.service_type}",
        )

    # Get the supply chain operation type from the service
    op_type = get_supply_chain_operation_type(service_class)

    if op_type is None:
        return None, ProjectionResult(
            operation_id=operation.operation_id,
            event_id="",
            event_type="",
            skipped=True,
            skip_reason=f"Service not decorated with supply chain semantics: {operation.service_type}",
        )

    # Project based on operation type
    event: TransformationEvent | TransactionEvent | ObjectEvent | AggregationEvent
    event_type_name: str

    match op_type:
        case SupplyChainOperationType.TRANSFORMATION:
            event = TransformationEvent.from_operation(
                operation_id=operation.operation_id,
                event_time=operation.started_at,
                transformation_type=operation.method_name,
            )
            event_type_name = "TransformationEvent"

        case SupplyChainOperationType.TRANSACTION:
            # For transaction events, we need additional data
            # This is a simplified projection - real implementations
            # would extract transaction details from operation metadata
            event = ObjectEvent(
                event_id=f"evt-{operation.operation_id}",
                event_time=operation.started_at,
                action=EventAction.OBSERVE,
                operation_id=operation.operation_id,
            )
            event_type_name = "ObjectEvent"  # Fallback until we have transaction details

        case SupplyChainOperationType.OBSERVATION:
            event = ObjectEvent.from_operation(
                operation_id=operation.operation_id,
                event_time=operation.started_at,
                action=EventAction.OBSERVE,
            )
            event_type_name = "ObjectEvent"

        case SupplyChainOperationType.AGGREGATION:
            # For aggregation events, we need parent_id
            # This is a simplified projection
            event = ObjectEvent(
                event_id=f"evt-{operation.operation_id}",
                event_time=operation.started_at,
                action=EventAction.ADD,
                operation_id=operation.operation_id,
            )
            event_type_name = "ObjectEvent"  # Fallback until we have aggregation details

        case _:
            return None, ProjectionResult(
                operation_id=operation.operation_id,
                event_id="",
                event_type="",
                skipped=True,
                skip_reason=f"Unknown operation type: {op_type}",
            )

    return event, ProjectionResult(
        operation_id=operation.operation_id,
        event_id=event.event_id,
        event_type=event_type_name,
        supply_chain_operation_type=op_type.value,
        skipped=False,
    )


@use_case
class ProjectExecutionUseCase:
    """Project a UseCaseExecution to UNTP traceability events.

    Iterates through the operation_records in the execution and projects
    each to the appropriate UNTP event type based on the service's
    supply chain semantics.

    One use case execution can produce multiple events (one per operation).
    Operations from services not decorated with supply chain semantics
    are skipped.
    """

    def __init__(self) -> None:
        pass  # No dependencies needed for projection

    async def execute(self, request: ProjectExecutionRequest) -> ProjectExecutionResponse:
        """Project all operations in an execution to UNTP events.

        Args:
            request: Contains the UseCaseExecution to project

        Returns:
            Response with projected events and projection results
        """
        execution = request.execution
        events: list[
            TransformationEvent | TransactionEvent | ObjectEvent | AggregationEvent
        ] = []
        results: list[ProjectionResult] = []

        for operation in execution.operation_records:
            event, result = _project_operation(operation)
            results.append(result)
            if event is not None:
                events.append(event)

        return ProjectExecutionResponse(
            events=events,
            projection_results=results,
            execution_id=execution.execution_id,
            event_count=len(events),
        )
