"""Temporal implementation of ExecutionService.

Returns the Temporal workflow ID as the execution identifier. Import this
only in workflow code — it must not be used outside a Temporal workflow context.
"""

from temporalio import workflow


class TemporalExecutionService:
    """ExecutionService implementation for Temporal workflows.

    Returns workflow.info().workflow_id so execution identity is stable
    across retries and replay. This must only be instantiated and used
    within a Temporal workflow.
    """

    def get_execution_id(self) -> str:
        """Return the Temporal workflow ID for this execution."""
        return workflow.info().workflow_id
