"""Core witness protocols for execution-agnostic use cases.

Provides ClockWitness and ExecutionWitness so use cases can obtain the
current time and execution identity without coupling to a specific
execution framework.

These are the two witnesses the framework ships, and every solution
injects them. A witness testifies to something about the execution
itself: its answer does not follow from its arguments, but the runtime
records what it said, so a workflow may call it inline and must not wrap
it in an activity (ADR 016).

They lived in ``julee.core.services`` until ADR 016 gave them a name.
That package remains as a deprecation shim.

See ADR 004: Execution-Agnostic Use Cases.
"""

from julee.core.witnesses.clock import ClockWitness, SystemClockWitness
from julee.core.witnesses.execution import DefaultExecutionWitness, ExecutionWitness

__all__ = [
    "ClockWitness",
    "DefaultExecutionWitness",
    "ExecutionWitness",
    "SystemClockWitness",
]
