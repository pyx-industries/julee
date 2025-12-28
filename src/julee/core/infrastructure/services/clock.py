"""ClockService implementations for non-Temporal contexts.

For Temporal workflows, use TemporalClockService from infrastructure/temporal/.
"""

from __future__ import annotations

from datetime import datetime, timezone


class SystemClockService:
    """ClockService implementation using system time.

    Use this for:
    - Production non-workflow code
    - CLI tools
    - Simple async execution

    For Temporal workflows, use TemporalClockService instead.
    """

    def now(self) -> datetime:
        """Return current system time as UTC datetime."""
        return datetime.now(timezone.utc)


class FixedClockService:
    """ClockService implementation returning a fixed time.

    Use this for:
    - Deterministic tests
    - Reproducing specific scenarios
    - Debugging time-dependent logic
    """

    def __init__(self, fixed_time: datetime) -> None:
        """Initialize with a fixed time.

        Args:
            fixed_time: The datetime to always return. Should be UTC.
        """
        if fixed_time.tzinfo is None:
            fixed_time = fixed_time.replace(tzinfo=timezone.utc)
        self._fixed_time = fixed_time

    def now(self) -> datetime:
        """Return the fixed time."""
        return self._fixed_time
