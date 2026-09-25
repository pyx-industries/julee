"""Temporal implementation of ClockWitness.

Uses workflow.now() for deterministic replay. Import this only in workflow
code — it must not be used outside a Temporal workflow context.
"""

from datetime import datetime


class TemporalClockWitness:
    """ClockWitness implementation for Temporal workflows.

    Delegates to workflow.now(), which Temporal records in the execution
    history, so a replay is told the same time. This must only be
    instantiated and used within a Temporal workflow.

    Never wrap this in an activity. The value is already in the history;
    an activity would add a round trip to fetch what the workflow holds
    (ADR 016).
    """

    def now(self) -> datetime:
        """Return the current workflow time (replay-stable)."""
        from temporalio import workflow

        return workflow.now()


TemporalClockService = TemporalClockWitness
"""Deprecated alias. See :mod:`julee.core.services`."""
