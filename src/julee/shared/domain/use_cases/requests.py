"""Request models for shared (core) use cases.

Following clean architecture principles, request models define the contract
between use cases and their callers.
"""

from pydantic import BaseModel, Field


class ListBoundedContextsRequest(BaseModel):
    """Request for listing bounded contexts.

    Empty for now but provides extension point for future filtering:
    - filter by structure type (domain/, flat)
    - filter by presence of specific layers
    - filter contrib vs non-contrib
    """

    pass


class GetBoundedContextRequest(BaseModel):
    """Request for getting a single bounded context by slug."""

    slug: str = Field(description="The bounded context slug (directory name)")


class ListCodeArtifactsRequest(BaseModel):
    """Request for listing code artifacts (entities, use cases, protocols).

    Optionally filter by bounded context.
    """

    bounded_context: str | None = Field(
        default=None, description="Filter to artifacts in this bounded context only"
    )


class GetCodeArtifactRequest(BaseModel):
    """Request for getting a single code artifact by name."""

    name: str = Field(description="The class name")
    bounded_context: str | None = Field(
        default=None, description="Bounded context to search in (optional)"
    )


# =============================================================================
# SemanticEvaluationService Requests
# =============================================================================


class EvaluateDocstringQualityRequest(BaseModel):
    """Request for evaluating docstring quality.

    Used by SemanticEvaluationService to assess whether a docstring
    adequately describes its subject.
    """

    docstring: str = Field(description="The docstring text to evaluate")
    context: str = Field(
        description="What the docstring describes (e.g., 'CreateInvoiceUseCase')"
    )


class EvaluateSingleResponsibilityRequest(BaseModel):
    """Request for evaluating single responsibility principle.

    Used by SemanticEvaluationService to assess whether a class
    has a single responsibility.
    """

    class_name: str = Field(description="Name of the class")
    class_docstring: str = Field(default="", description="Class docstring")
    method_names: list[str] = Field(
        default_factory=list, description="Names of public methods in the class"
    )
    field_names: list[str] = Field(
        default_factory=list, description="Names of fields/attributes in the class"
    )


class EvaluateNamingQualityRequest(BaseModel):
    """Request for evaluating naming quality.

    Used by SemanticEvaluationService to assess whether a name
    is meaningful and appropriate.
    """

    name: str = Field(description="The identifier name to evaluate")
    kind: str = Field(description="What it is: 'class', 'method', 'variable', 'field'")
    context: str = Field(
        default="", description="Surrounding context (class name, module, etc.)"
    )


class EvaluateMethodComplexityRequest(BaseModel):
    """Request for evaluating method complexity.

    Used by SemanticEvaluationService to assess whether a method
    is too complex.
    """

    method_source: str = Field(description="The method's source code")
    method_name: str = Field(description="The name of the method")
