"""ClockService protocol and default implementations.

Use cases inject ClockService to obtain the current time without coupling to
system time or any specific execution framework.

See ADR 004: Execution-Agnostic Use Cases.
"""

from datetime import UTC, datetime
from typing import Protocol


class ClockService(Protocol):
    """Service protocol for obtaining the current time.

    Use cases needing the current time MUST inject ClockService and call
    clock_service.now() instead of calling datetime.now() directly.
    This enables deterministic testing and framework-agnostic execution.
    """

    def now(self) -> datetime:
        """Return the current time as a timezone-aware datetime (UTC)."""
        ...


class SystemClockService:
    """ClockService implementation using system time.

    Use this in non-workflow contexts: API handlers, CLI commands, tests
    that need real time. For Temporal workflows use TemporalClockService.
    """

    def now(self) -> datetime:
        """Return the current system time in UTC."""
        return datetime.now(UTC)
