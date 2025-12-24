"""Pipeline model for Temporal workflow wrappers."""

from pydantic import BaseModel, Field, field_validator

from julee.shared.domain.models.code_info import MethodInfo


class Pipeline(BaseModel):
    """A durable execution wrapper that keeps business logic pure.

    Long-running processes need durability. They need to survive crashes,
    handle retries, and resume from checkpoints. Temporal provides this -
    but if your use case is littered with Temporal decorators and workflow
    primitives, you've violated the Dependency Rule. Your business logic
    now depends on infrastructure.

    The pipeline pattern solves this. The pipeline is a thin wrapper that
    lives in infrastructure. It has the Temporal decorators. It handles
    the durability concerns. But its run() method does exactly one thing:
    call the use case's execute() method. All business logic stays in the
    use case, which knows nothing about Temporal.

    This separation means you can test your use case with a simple unit
    test - no Temporal test server needed. The use case is pure. The
    pipeline is just plumbing that makes it durable.

    When Temporal is replaced by the next workflow engine, you rewrite
    the pipelines. The use cases - your actual business logic - remain
    untouched. That's the whole point.
    """

    name: str
    docstring: str = ""
    file: str = ""
    bounded_context: str = ""
    has_workflow_decorator: bool = False
    has_run_decorator: bool = False
    has_run_method: bool = False
    wrapped_use_case: str | None = None
    delegates_to_use_case: bool = False
    methods: list[MethodInfo] = Field(default_factory=list)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @property
    def expected_use_case_name(self) -> str | None:
        """Derive the expected use case name from pipeline name.

        Example: NewDataDetectionPipeline -> NewDataDetectionUseCase
                 ExtractAssemblePipeline -> ExtractAssembleUseCase or ExtractAssembleDataUseCase
        """
        from julee.shared.domain.doctrine_constants import (
            PIPELINE_SUFFIX,
            USE_CASE_SUFFIX,
        )

        if not self.name.endswith(PIPELINE_SUFFIX):
            return None
        prefix = self.name[: -len(PIPELINE_SUFFIX)]
        return f"{prefix}{USE_CASE_SUFFIX}"

    @property
    def is_compliant(self) -> bool:
        """Check if pipeline follows doctrine pattern.

        A compliant pipeline:
        1. Has @workflow.defn decorator
        2. Has run() method with @workflow.run decorator
        3. Delegates to a UseCase (doesn't contain business logic directly)
        """
        return (
            self.has_workflow_decorator
            and self.has_run_method
            and self.has_run_decorator
            and self.delegates_to_use_case
        )
