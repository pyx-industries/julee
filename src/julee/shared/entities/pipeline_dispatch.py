"""Pipeline dispatch models for tracking child pipeline execution.

These models record what pipelines were dispatched, with what requests,
and what responses were received (or errors encountered).

See: docs/architecture/proposals/pipeline_router_design.md
"""

from pydantic import BaseModel


class PipelineDispatchItem(BaseModel):
    """Record of a dispatched child pipeline.

    Tracks the full lifecycle of a child pipeline dispatch:
    - What pipeline was called
    - What request was sent
    - What response was received (or error if failed)

    This provides full traceability of the workflow execution chain.
    """

    pipeline: str
    request: dict
    response: dict | None = None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        """Check if the dispatch completed successfully."""
        return self.response is not None and self.error is None

    @property
    def failed(self) -> bool:
        """Check if the dispatch failed."""
        return self.error is not None
