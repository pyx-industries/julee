"""Request and response models for code artifact listing use cases.

These are the Request/Response models used across the list_* use cases
in the code_artifact module.
"""

from pydantic import BaseModel, Field

from julee.core.entities import ClassInfo, Pipeline


class CodeArtifactWithContext(BaseModel):
    """A code artifact with its bounded context slug."""

    artifact: ClassInfo
    bounded_context: str = Field(description="Slug of the bounded context")


class ListCodeArtifactsRequest(BaseModel):
    """Request for listing code artifacts.

    Optionally filter by bounded context.
    """

    bounded_context: str | None = Field(
        default=None, description="Filter to artifacts in this bounded context only"
    )


class ListCodeArtifactsResponse(BaseModel):
    """Response from listing code artifacts."""

    artifacts: list[CodeArtifactWithContext]


class ListPipelinesResponse(BaseModel):
    """Response from listing pipelines."""

    pipelines: list[Pipeline]
