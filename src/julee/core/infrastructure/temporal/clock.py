"""Temporal-aware ClockService implementation.

Wraps Temporal's workflow.now() for deterministic replay in workflows.
"""

from __future__ import annotations

from datetime import datetime

from temporalio import workflow


class TemporalClockService:
    """ClockService implementation for Temporal workflows.

    Uses workflow.now() which returns deterministic time during replay,
    ensuring workflow executions are reproducible.

    Only use this within Temporal workflow code. For activities or
    non-workflow code, use SystemClockService.
    """

    def now(self) -> datetime:
        """Return current workflow time.

        During initial execution, returns actual current time.
        During replay, returns the recorded time from history.
        """
        return workflow.now()
