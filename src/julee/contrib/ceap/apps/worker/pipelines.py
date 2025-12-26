"""
Doctrine-compliant Temporal workflows (pipelines) for CEAP document operations.

This module contains the refactored pipelines that follow the Pipeline doctrine:
- Pipeline wraps exactly one business UseCase
- run() is the single entry point with @workflow.run
- run_next() handles routing (no decorator)
- Business logic stays in UseCase, not Pipeline

Pipelines included:
- ExtractAssemblePipeline: Orchestrates document extraction and assembly
- ValidateDocumentPipeline: Orchestrates document policy validation

See: docs/architecture/proposals/pipeline_router_design.md
"""

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from julee.contrib.ceap.infrastructure.temporal.repositories.proxies import (
    WorkflowAssemblyRepositoryProxy,
    WorkflowAssemblySpecificationRepositoryProxy,
    WorkflowDocumentPolicyValidationRepositoryProxy,
    WorkflowDocumentRepositoryProxy,
    WorkflowKnowledgeServiceConfigRepositoryProxy,
    WorkflowKnowledgeServiceQueryRepositoryProxy,
    WorkflowPolicyRepositoryProxy,
)
from julee.contrib.ceap.infrastructure.temporal.services.proxies import (
    WorkflowKnowledgeServiceProxy,
)
from julee.contrib.ceap.use_cases import (
    ExtractAssembleDataRequest,
    ExtractAssembleDataUseCase,
    ValidateDocumentRequest,
    ValidateDocumentUseCase,
)
from julee.core.entities.pipeline_dispatch import PipelineDispatchItem


@workflow.defn
class ExtractAssemblePipeline:
    """
    Doctrine-compliant pipeline for document extract and assemble operations.

    This pipeline wraps ExtractAssembleDataUseCase and provides:
    1. Temporal durability guarantees
    2. Routing to downstream pipelines via run_next()
    3. Full dispatch traceability in response

    The pipeline is thin - business logic is in ExtractAssembleDataUseCase.
    """

    def __init__(self) -> None:
        self.current_step = "initialized"
        self.assembly_id: str | None = None

    @workflow.query
    def get_current_step(self) -> str:
        """Query method to get the current workflow step."""
        return self.current_step

    @workflow.query
    def get_assembly_id(self) -> str | None:
        """Query method to get the assembly ID once created."""
        return self.assembly_id

    @workflow.run
    async def run(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the extract and assemble pipeline.

        Args:
            request: Serialized ExtractAssembleDataRequest (dict from Temporal)

        Returns:
            Serialized response with assembly data and dispatches
        """
        self.current_step = "validating_request"

        # Convert dict to Request (Temporal serializes as dict)
        assemble_request = ExtractAssembleDataRequest.model_validate(request)

        workflow.logger.info(
            "Starting extract assemble pipeline",
            extra={
                "document_id": assemble_request.document_id,
                "assembly_specification_id": assemble_request.assembly_specification_id,
                "workflow_id": workflow.info().workflow_id,
            },
        )

        self.current_step = "creating_use_case"

        # Create workflow-safe repository proxies
        document_repo = WorkflowDocumentRepositoryProxy()  # type: ignore[abstract]
        assembly_repo = WorkflowAssemblyRepositoryProxy()  # type: ignore[abstract]
        assembly_specification_repo = (
            WorkflowAssemblySpecificationRepositoryProxy()  # type: ignore[abstract]
        )
        knowledge_service_query_repo = (
            WorkflowKnowledgeServiceQueryRepositoryProxy()  # type: ignore[abstract]
        )
        knowledge_service_config_repo = (
            WorkflowKnowledgeServiceConfigRepositoryProxy()  # type: ignore[abstract]
        )
        knowledge_service = WorkflowKnowledgeServiceProxy()  # type: ignore[abstract]

        # Create the use case with workflow-safe repositories
        use_case = ExtractAssembleDataUseCase(
            document_repo=document_repo,
            assembly_repo=assembly_repo,
            assembly_specification_repo=assembly_specification_repo,
            knowledge_service_query_repo=knowledge_service_query_repo,
            knowledge_service_config_repo=knowledge_service_config_repo,
            knowledge_service=knowledge_service,
            now_fn=workflow.now,
        )

        self.current_step = "executing_use_case"

        # Execute business UseCase - delegates all business logic
        assembly = await use_case.execute(assemble_request)

        self.assembly_id = assembly.assembly_id
        self.current_step = "routing"

        # Build response with assembly data
        response = {
            "assembly_id": assembly.assembly_id,
            "assembly_specification_id": assembly.assembly_specification_id,
            "input_document_id": assembly.input_document_id,
            "assembled_document_id": assembly.assembled_document_id,
            "status": assembly.status.value,
            "workflow_id": assembly.workflow_id,
        }

        # Route to downstream pipelines
        dispatches = await self.run_next(response)
        response["dispatches"] = [d.model_dump() for d in dispatches]

        self.current_step = "completed"

        workflow.logger.info(
            "Extract assemble pipeline completed",
            extra={
                "assembly_id": assembly.assembly_id,
                "assembled_document_id": assembly.assembled_document_id,
                "status": assembly.status.value,
                "dispatch_count": len(dispatches),
            },
        )

        return response

    async def run_next(self, response: dict[str, Any]) -> list[PipelineDispatchItem]:
        """
        Route response to downstream pipelines.

        Args:
            response: The response from the UseCase

        Returns:
            List of PipelineDispatchItem records tracking what was dispatched

        Note: This method does NOT have @workflow.run - it's a helper method.
        """
        # CEAP pipelines don't currently have downstream routing configured
        # This is a stub for future routing implementation
        workflow.logger.debug(
            "run_next called - no downstream routes configured",
            extra={"assembly_id": response.get("assembly_id")},
        )
        return []

    @workflow.signal
    async def cancel_assembly(self, reason: str) -> None:
        """
        Signal handler to cancel the assembly process.

        Args:
            reason: Reason for cancellation
        """
        workflow.logger.info(
            "Assembly cancellation requested",
            extra={
                "assembly_id": self.assembly_id,
                "reason": reason,
                "current_step": self.current_step,
            },
        )


@workflow.defn
class ValidateDocumentPipeline:
    """
    Doctrine-compliant pipeline for document validation operations.

    This pipeline wraps ValidateDocumentUseCase and provides:
    1. Temporal durability guarantees
    2. Routing to downstream pipelines via run_next()
    3. Full dispatch traceability in response

    The pipeline is thin - business logic is in ValidateDocumentUseCase.
    """

    def __init__(self) -> None:
        self.current_step = "initialized"
        self.validation_id: str | None = None

    @workflow.query
    def get_current_step(self) -> str:
        """Query method to get the current workflow step."""
        return self.current_step

    @workflow.query
    def get_validation_id(self) -> str | None:
        """Query method to get the validation ID once created."""
        return self.validation_id

    @workflow.run
    async def run(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the document validation pipeline.

        Args:
            request: Serialized ValidateDocumentRequest (dict from Temporal)

        Returns:
            Serialized response with validation data and dispatches
        """
        self.current_step = "validating_request"

        # Convert dict to Request (Temporal serializes as dict)
        validate_request = ValidateDocumentRequest.model_validate(request)

        workflow.logger.info(
            "Starting document validation pipeline",
            extra={
                "document_id": validate_request.document_id,
                "policy_id": validate_request.policy_id,
                "workflow_id": workflow.info().workflow_id,
            },
        )

        self.current_step = "creating_use_case"

        # Create workflow-safe repository proxies
        document_repo = WorkflowDocumentRepositoryProxy()  # type: ignore[abstract]
        knowledge_service_query_repo = (
            WorkflowKnowledgeServiceQueryRepositoryProxy()  # type: ignore[abstract]
        )
        knowledge_service_config_repo = (
            WorkflowKnowledgeServiceConfigRepositoryProxy()  # type: ignore[abstract]
        )
        policy_repo = WorkflowPolicyRepositoryProxy()  # type: ignore[abstract]
        document_policy_validation_repo = (
            WorkflowDocumentPolicyValidationRepositoryProxy()  # type: ignore[abstract]
        )
        knowledge_service = WorkflowKnowledgeServiceProxy()  # type: ignore[abstract]

        # Create the use case with workflow-safe repositories
        use_case = ValidateDocumentUseCase(
            document_repo=document_repo,
            knowledge_service_query_repo=knowledge_service_query_repo,
            knowledge_service_config_repo=knowledge_service_config_repo,
            policy_repo=policy_repo,
            document_policy_validation_repo=document_policy_validation_repo,
            knowledge_service=knowledge_service,
            now_fn=workflow.now,
        )

        self.current_step = "executing_use_case"

        # Execute business UseCase - delegates all business logic
        validation = await use_case.execute(validate_request)

        self.validation_id = validation.validation_id
        self.current_step = "routing"

        # Build response with validation data
        response = {
            "validation_id": validation.validation_id,
            "input_document_id": validation.input_document_id,
            "policy_id": validation.policy_id,
            "status": validation.status.value,
            "passed": validation.passed,
            "validation_scores": validation.validation_scores,
            "transformed_document_id": validation.transformed_document_id,
            "post_transform_validation_scores": validation.post_transform_validation_scores,
        }

        # Route to downstream pipelines
        dispatches = await self.run_next(response)
        response["dispatches"] = [d.model_dump() for d in dispatches]

        self.current_step = "completed"

        workflow.logger.info(
            "Document validation pipeline completed",
            extra={
                "validation_id": validation.validation_id,
                "status": validation.status.value,
                "passed": validation.passed,
                "dispatch_count": len(dispatches),
            },
        )

        return response

    async def run_next(self, response: dict[str, Any]) -> list[PipelineDispatchItem]:
        """
        Route response to downstream pipelines.

        Args:
            response: The response from the UseCase

        Returns:
            List of PipelineDispatchItem records tracking what was dispatched

        Note: This method does NOT have @workflow.run - it's a helper method.
        """
        # CEAP pipelines don't currently have downstream routing configured
        # This is a stub for future routing implementation
        workflow.logger.debug(
            "run_next called - no downstream routes configured",
            extra={"validation_id": response.get("validation_id")},
        )
        return []

    @workflow.signal
    async def cancel_validation(self, reason: str) -> None:
        """
        Signal handler to cancel the validation process.

        Args:
            reason: Reason for cancellation
        """
        workflow.logger.info(
            "Validation cancellation requested",
            extra={
                "validation_id": self.validation_id,
                "reason": reason,
                "current_step": self.current_step,
            },
        )


# Workflow configuration with retry policies optimized for document processing
EXTRACT_ASSEMBLE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=5,
    non_retryable_error_types=["ValueError"],  # Don't retry validation errors
)

# Workflow configuration with retry policies optimized for document validation
VALIDATE_DOCUMENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=3,
    non_retryable_error_types=["ValueError"],  # Don't retry validation errors
)


# Export the pipelines
__all__ = [
    "ExtractAssemblePipeline",
    "ValidateDocumentPipeline",
    "EXTRACT_ASSEMBLE_RETRY_POLICY",
    "VALIDATE_DOCUMENT_RETRY_POLICY",
]
