"""Response models for shared (core) use cases.

Response models wrap domain models, enabling pagination and additional
metadata while maintaining type safety.
"""

from pydantic import BaseModel, Field

from julee.shared.domain.models import BoundedContext, ClassInfo, PipelineInfo


class ListBoundedContextsResponse(BaseModel):
    """Response from listing bounded contexts."""

    bounded_contexts: list[BoundedContext]


class GetBoundedContextResponse(BaseModel):
    """Response from getting a single bounded context."""

    bounded_context: BoundedContext | None


class CodeArtifactWithContext(BaseModel):
    """A code artifact with its bounded context slug."""

    artifact: ClassInfo
    bounded_context: str = Field(description="Slug of the bounded context")


class ListCodeArtifactsResponse(BaseModel):
    """Response from listing code artifacts."""

    artifacts: list[CodeArtifactWithContext]


class GetCodeArtifactResponse(BaseModel):
    """Response from getting a single code artifact."""

    artifact: CodeArtifactWithContext | None


class ListPipelinesResponse(BaseModel):
    """Response from listing pipelines."""

    pipelines: list[PipelineInfo]
