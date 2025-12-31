"""PipelineOutput entity for tracking artifacts produced by pipelines.

A PipelineOutput represents an artifact produced by pipeline execution.
This could be a document, a credential, a processed file, or any other
output. The entity links the output to the executions that produced it.

UNTP's DigitalProductPassport is projected from PipelineOutput, linking
the product to all the traceability events that record its provenance.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PipelineOutput(BaseModel):
    """Immutable record of an artifact produced by pipeline execution.

    Tracks what was produced, when, by which pipeline, and links to
    the execution records that document its provenance.

    Use cases:
    - Output tracking (what artifacts exist, where they came from)
    - Supply chain projection (output → Digital Product Passport)
    - Provenance queries (given an output, find all operations)
    - Compliance (link outputs to audit trail)
    """

    model_config = ConfigDict(frozen=True)

    output_id: str
    """Unique identifier for this output."""

    pipeline_slug: str
    """Slug of the pipeline that produced this output."""

    name: str
    """Human-readable name for the output."""

    created_at: datetime
    """When the output was created."""

    execution_ids: list[str] = Field(default_factory=list)
    """IDs of UseCaseExecutions involved in producing this output."""

    artifact_uri: str | None = None
    """Optional URI where the artifact is stored."""

    content_hash: str | None = None
    """Optional hash of the content for integrity verification."""

    content_type: str | None = None
    """Optional MIME type of the content."""

    metadata: dict = Field(default_factory=dict)
    """Additional metadata about the output."""

    @property
    def has_artifact(self) -> bool:
        """Whether this output has a stored artifact."""
        return self.artifact_uri is not None
