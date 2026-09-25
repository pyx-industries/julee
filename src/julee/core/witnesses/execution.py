"""ExecutionWitness protocol and default implementations.

Use cases inject ExecutionWitness to obtain a unique execution identifier
without coupling to a specific execution framework like Temporal.

See ADR 004: Execution-Agnostic Use Cases, and ADR 016: Naming the Driven
Ports.
"""

import uuid
from typing import Protocol


class ExecutionWitness(Protocol):
    """Witness protocol for execution-level context.

    Provides a unique identifier for the current execution without coupling
    use cases to Temporal's workflow_id or any other framework concept.

    In Temporal: backed by workflow.info().workflow_id
    In tests: backed by a deterministic or randomly generated UUID
    In simple async: backed by a generated UUID

    A witness rather than a calculator (ADR 016): the identifier does not
    follow from any argument, and a fresh one is minted where no runtime
    supplies it. It is safe to call from workflow code because the runtime
    records the identity and a replay is told the same thing, and it must
    not be wrapped in an activity for the same reason.
    """

    def get_execution_id(self) -> str:
        """Return a unique identifier for this execution."""
        ...


class DefaultExecutionWitness:
    """Default ExecutionWitness generating a UUID per instance.

    Use this in non-workflow contexts: API handlers, CLI commands, tests.
    For Temporal workflows use TemporalExecutionWitness.
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
