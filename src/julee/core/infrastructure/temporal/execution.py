"""Temporal-aware ExecutionService implementation.

Provides workflow_id as execution identity within Temporal workflows.
"""

from __future__ import annotations

from temporalio import workflow


class TemporalExecutionService:
    """ExecutionService implementation for Temporal workflows.

    Returns the workflow_id from workflow.info(), providing stable
    execution identity throughout a workflow's lifecycle.

    Only use this within Temporal workflow code. For activities or
    non-workflow code, use DefaultExecutionService.
    """

    def get_execution_id(self) -> str:
        """Return the Temporal workflow ID.

        The workflow_id is stable across the entire workflow execution,
        including retries and continue-as-new.
        """
        return workflow.info().workflow_id
