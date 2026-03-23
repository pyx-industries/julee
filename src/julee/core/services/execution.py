"""ExecutionService protocol and default implementations.

Use cases inject ExecutionService to obtain a unique execution identifier
without coupling to a specific execution framework like Temporal.

See ADR 004: Execution-Agnostic Use Cases.
"""

import uuid
from typing import Protocol


class ExecutionService(Protocol):
    """Service protocol for execution-level context.

    Provides a unique identifier for the current execution without coupling
    use cases to Temporal's workflow_id or any other framework concept.

    In Temporal: backed by workflow.info().workflow_id
    In tests: backed by a deterministic or randomly generated UUID
    In simple async: backed by a generated UUID
    """

    def get_execution_id(self) -> str:
        """Return a unique identifier for this execution."""
        ...


class DefaultExecutionService:
    """Default ExecutionService generating a UUID per instance.

    Use this in non-workflow contexts: API handlers, CLI commands, tests.
    For Temporal workflows use TemporalExecutionService.
    """

    def __init__(self, execution_id: str | None = None) -> None:
        """Initialise with an optional fixed execution ID.

        Args:
            execution_id: Fixed ID to return. If omitted, a random UUID is
                generated. Pass a fixed value in tests for determinism.
        """
        self._execution_id = execution_id or str(uuid.uuid4())

    def get_execution_id(self) -> str:
        """Return the execution ID."""
        return self._execution_id
