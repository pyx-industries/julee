"""Temporal implementation of ClockService.

Uses workflow.now() for deterministic replay. Import this only in workflow
code — it must not be used outside a Temporal workflow context.
"""

from datetime import datetime


class TemporalClockService:
    """ClockService implementation for Temporal workflows.

    Delegates to workflow.now() so time is deterministic during replay.
    This must only be instantiated and used within a Temporal workflow.
    """

    def now(self) -> datetime:
        """Return the current workflow time (deterministic during replay)."""
        from temporalio import workflow

        return workflow.now()
