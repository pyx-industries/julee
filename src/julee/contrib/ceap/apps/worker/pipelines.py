"""
Temporal workflows (pipelines) for CEAP document operations.

This module contains the refactored pipelines that follow the Pipeline doctrine:
- Pipeline wraps exactly one business UseCase
- run() is the single entry point with @workflow.run
- Business logic stays in UseCase, not Pipeline

Pipelines included:
- ExtractAssembleWorkflow: Orchestrates document extraction and assembly
- ValidateDocumentWorkflow: Orchestrates document policy validation

See: docs/architecture/proposals/pipeline_router_design.md
"""

import logging
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from julee.contrib.ceap.entities.assembly import Assembly
from julee.contrib.ceap.entities.document_policy_validation import (
    DocumentPolicyValidation,
)
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

logger = logging.getLogger(__name__)


@workflow.defn
class ExtractAssembleWorkflow:
    """
    Temporal workflow for document extract and assemble operations.

    This workflow:
    1. Receives document_id and assembly_specification_id
    2. Orchestrates the ExtractAssembleDataUseCase with workflow-safe proxies
    3. Provides durability and retry logic for long-running assembly
    4. Returns the completed Assembly object

    The workflow remains framework-agnostic by delegating all business logic
    to the use case, while providing Temporal-specific orchestration concerns
    like retry policies, timeouts, and state management.
    """

    def __init__(self) -> None:
        self.current_step = "initialized"
        self.assembly_id: str | None = None

    @workflow.query
    def get_current_step(self) -> str:
        """Query method to get the current workflow step"""
        return self.current_step

    @workflow.query
    def get_assembly_id(self) -> str | None:
        """Query method to get the assembly ID once created"""
        return self.assembly_id

    @workflow.run
    async def run(self, document_id: str, assembly_specification_id: str) -> Assembly:
        """
        Execute the extract and assemble workflow.

        Args:
            document_id: ID of the document to assemble
            assembly_specification_id: ID of the specification to use

        Returns:
            Completed Assembly object with assembled document

        Raises:
            ValueError: If required entities are not found
            RuntimeError: If assembly processing fails after retries
        """
        workflow.logger.info(
            "Starting extract assemble workflow",
            extra={
                "document_id": document_id,
                "assembly_specification_id": assembly_specification_id,
                "workflow_id": workflow.info().workflow_id,
                "run_id": workflow.info().run_id,
            },
        )

        self.current_step = "initializing_repositories"

        try:
            # Create workflow-safe repository proxies
            # These proxy all calls through Temporal activities for durability
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

            workflow.logger.debug(
                "Repository proxies created",
                extra={
                    "document_id": document_id,
                    "assembly_specification_id": assembly_specification_id,
                },
            )

            self.current_step = "creating_use_case"

            # Create workflow-safe knowledge service proxy
            knowledge_service = WorkflowKnowledgeServiceProxy()  # type: ignore[abstract]

            # Create the use case with workflow-safe repositories
            # The use case remains completely unaware it's running in workflow
            use_case = ExtractAssembleDataUseCase(
                document_repo=document_repo,
                assembly_repo=assembly_repo,
                assembly_specification_repo=assembly_specification_repo,
                knowledge_service_query_repo=knowledge_service_query_repo,
                knowledge_service_config_repo=knowledge_service_config_repo,
                knowledge_service=knowledge_service,
                now_fn=workflow.now,
            )

            workflow.logger.debug(
                "Use case created successfully",
                extra={
                    "document_id": document_id,
                    "assembly_specification_id": assembly_specification_id,
                },
            )

            self.current_step = "executing_assembly"

            # Execute the assembly process with workflow durability
            # All repository calls inside the use case will be executed as
            # Temporal activities with automatic retry and state persistence
            request = ExtractAssembleDataRequest(
                document_id=document_id,
                assembly_specification_id=assembly_specification_id,
                workflow_id=workflow.info().workflow_id,
            )
            assembly = await use_case.assemble_data(request)

            # Store the assembly ID for queries
            self.assembly_id = assembly.assembly_id

            self.current_step = "completed"

            workflow.logger.info(
                "Extract assemble workflow completed successfully",
                extra={
                    "document_id": document_id,
                    "assembly_specification_id": assembly_specification_id,
                    "assembly_id": assembly.assembly_id,
                    "assembled_document_id": assembly.assembled_document_id,
                    "status": assembly.status.value,
                },
            )

            return assembly

        except Exception as e:
            self.current_step = "failed"

            workflow.logger.error(
                "Extract assemble workflow failed",
                extra={
                    "document_id": document_id,
                    "assembly_specification_id": assembly_specification_id,
                    "assembly_id": self.assembly_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            # Re-raise to let Temporal handle retry logic
            raise

    @workflow.signal
    async def cancel_assembly(self, reason: str) -> None:
        """
        Signal handler to cancel the assembly process.

        Args:
            reason: Reason for cancellation

        Note:
            This is a placeholder for future cancellation logic.
            Currently, we rely on Temporal's built-in workflow cancellation.
        """
        workflow.logger.info(
            "Assembly cancellation requested",
            extra={
                "assembly_id": self.assembly_id,
                "reason": reason,
                "current_step": self.current_step,
            },
        )

        # Future: Implement graceful cancellation logic here
        # For now, let the workflow be cancelled naturally by Temporal


@workflow.defn
class ValidateDocumentWorkflow:
    """
    Temporal workflow for document validation operations.

    This workflow:
    1. Receives document_id and policy_id
    2. Orchestrates the ValidateDocumentUseCase with workflow-safe proxies
    3. Provides durability and retry logic for validation processing
    4. Returns the completed DocumentPolicyValidation object

    The workflow remains framework-agnostic by delegating all business logic
    to the use case, while providing Temporal-specific orchestration concerns
    like retry policies, timeouts, and state management.
    """

    def __init__(self) -> None:
        self.current_step = "initialized"
        self.validation_id: str | None = None

    @workflow.query
    def get_current_step(self) -> str:
        """Query method to get the current workflow step"""
        return self.current_step

    @workflow.query
    def get_validation_id(self) -> str | None:
        """Query method to get the validation ID once created"""
        return self.validation_id

    @workflow.run
    async def run(self, document_id: str, policy_id: str) -> DocumentPolicyValidation:
        """
        Execute the document validation workflow.

        Args:
            document_id: ID of the document to validate
            policy_id: ID of the policy to validate against

        Returns:
            Completed DocumentPolicyValidation object with validation results

        Raises:
            ValueError: If required entities are not found
            RuntimeError: If validation processing fails after retries
        """
        workflow.logger.info(
            "Starting document validation workflow",
            extra={
                "document_id": document_id,
                "policy_id": policy_id,
                "workflow_id": workflow.info().workflow_id,
                "run_id": workflow.info().run_id,
            },
        )

        self.current_step = "initializing_repositories"

        try:
            # Create workflow-safe repository proxies
            # These proxy all calls through Temporal activities for durability
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

            workflow.logger.debug(
                "Repository proxies created",
                extra={
                    "document_id": document_id,
                    "policy_id": policy_id,
                },
            )

            self.current_step = "creating_use_case"

            # Create workflow-safe knowledge service proxy
            knowledge_service = WorkflowKnowledgeServiceProxy()  # type: ignore[abstract]

            # Create the use case with workflow-safe repositories
            # The use case remains completely unaware it's running in workflow
            use_case = ValidateDocumentUseCase(
                document_repo=document_repo,
                knowledge_service_query_repo=knowledge_service_query_repo,
                knowledge_service_config_repo=knowledge_service_config_repo,
                policy_repo=policy_repo,
                document_policy_validation_repo=document_policy_validation_repo,
                knowledge_service=knowledge_service,
                now_fn=workflow.now,
            )

            workflow.logger.debug(
                "Use case created successfully",
                extra={
                    "document_id": document_id,
                    "policy_id": policy_id,
                },
            )

            self.current_step = "executing_validation"

            # Execute the validation process with workflow durability
            # All repository calls inside the use case will be executed as
            # Temporal activities with automatic retry and state persistence
            request = ValidateDocumentRequest(
                document_id=document_id,
                policy_id=policy_id,
            )
            validation = await use_case.validate_document(request)

            # Store the validation ID for queries
            self.validation_id = validation.validation_id

            self.current_step = "completed"

            workflow.logger.info(
                "Document validation workflow completed successfully",
                extra={
                    "document_id": document_id,
                    "policy_id": policy_id,
                    "validation_id": validation.validation_id,
                    "status": validation.status.value,
                    "passed": validation.passed,
                },
            )

            return validation

        except Exception as e:
            self.current_step = "failed"

            workflow.logger.error(
                "Document validation workflow failed",
                extra={
                    "document_id": document_id,
                    "policy_id": policy_id,
                    "validation_id": self.validation_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            # Re-raise to let Temporal handle retry logic
            raise

    @workflow.signal
    async def cancel_validation(self, reason: str) -> None:
        """
        Signal handler to cancel the validation process.

        Args:
            reason: Reason for cancellation

        Note:
            This is a placeholder for future cancellation logic.
            Currently, we rely on Temporal's built-in workflow cancellation.
        """
        workflow.logger.info(
            "Validation cancellation requested",
            extra={
                "validation_id": self.validation_id,
                "reason": reason,
                "current_step": self.current_step,
            },
        )

        # Future: Implement graceful cancellation logic here
        # For now, let the workflow be cancelled naturally by Temporal


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
    "ExtractAssembleWorkflow",
    "ValidateDocumentWorkflow",
    "EXTRACT_ASSEMBLE_RETRY_POLICY",
    "VALIDATE_DOCUMENT_RETRY_POLICY",
]
