"""Pipeline model for Temporal workflow wrappers.

A Julee pipeline is a use case that has been appropriately treated (with
decorators and proxies) to run as a Temporal workflow.

A pipeline is the marriage of two things:

1. A **Julee use case** - deterministic business logic following Clean Architecture
2. **Temporal workflow technology** - durable, reliable execution with automatic retries

All Julee pipelines are Temporal workflows, but not all Temporal workflows are
Julee pipelines. All Julee pipelines are Julee use cases, but not all Julee
use cases are pipelines.

Why Pipelines?
--------------
Direct execution of use cases is simple but fragile:

- If the process crashes, work is lost
- If a service fails, the operation fails
- No record of what happened or why
- No way to retry or recover

Pipelines solve these problems:

**Reliability** - Automatic retries, timeout handling, failure recovery. If a
service is temporarily unavailable, the pipeline waits and retries.

**Durability** - Workflow state is persisted. If the worker crashes, another
worker picks up where it left off.

**Observability** - Julee uses Temporal's workflow history as an audit log.
Every step is recorded: what happened, when, with what inputs and outputs.

**Supply Chain Provenance** - The audit log constructs a supply chain provenance
graph for artefacts produced by the pipeline. Every step is recorded with its
actor, inputs, outputs, and timing - creating complete lineage for compliance.

Pipeline Proxies
----------------
When a use case runs as a pipeline, its repository and service dependencies are
replaced with proxy classes that route calls through Temporal activities. The
proxy implements the same protocol, enabling dependency injection to swap
implementations. But each method call becomes a Temporal activity with its own
timeout, retry policy, state persistence, and audit trail.
"""

from pydantic import BaseModel, Field, field_validator

from julee.core.entities.code_info import MethodInfo


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

    # run_next() pattern attributes
    has_run_next_method: bool = False
    run_next_has_workflow_decorator: bool = False
    run_calls_run_next: bool = False
    sets_dispatches_on_response: bool = False

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
        from julee.core.doctrine_constants import (
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
