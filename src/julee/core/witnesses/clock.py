"""ClockWitness protocol and default implementations.

Use cases inject ClockWitness to obtain the current time without coupling to
system time or any specific execution framework.

See ADR 004: Execution-Agnostic Use Cases, and ADR 016: Naming the Driven
Ports.
"""

from datetime import UTC, datetime
from typing import Protocol


class ClockWitness(Protocol):
    """Witness protocol for obtaining the current time.

    Use cases needing the current time MUST inject ClockWitness and call
    ``now()`` instead of calling ``datetime.now()`` directly. This enables
    deterministic testing and framework-agnostic execution.

    A witness rather than a calculator (ADR 016): its answer does not
    follow from domain arguments. It need not change on every call; a test
    clock can return a fixed time. Workflow code must use a workflow-backed
    implementation such as TemporalClockWitness, whose time is replay-stable.
    Injecting this protocol alone does not make a system clock replay-safe.

    The workflow-backed implementation must **not** be wrapped in an activity:
    it reads time the workflow runtime already holds.
    """

    def now(self) -> datetime:
        """Return the current time as a timezone-aware datetime (UTC)."""
        ...


class SystemClockWitness:
    """ClockWitness implementation using system time.

    Use this in non-workflow contexts: API handlers, CLI commands, tests
    that need real time. For Temporal workflows use TemporalClockWitness.

    Not replay-stable, and never will be — which is the point of the port
    having two implementations rather than one. Replay-stability belongs
    to the runtime, not to the protocol.
    """

    def now(self) -> datetime:
        """Return the current system time in UTC."""
        return datetime.now(UTC)
