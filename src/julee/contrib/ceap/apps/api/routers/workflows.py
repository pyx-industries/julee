"""Workflows API router for workflow management."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from temporalio.client import Client

from julee.contrib.ceap.apps.worker import TASK_QUEUE as CEAP_TASK_QUEUE
from julee.contrib.ceap.apps.worker.pipelines import (
    EXTRACT_ASSEMBLE_RETRY_POLICY,
    ExtractAssemblePipeline,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models for workflow operations
# These are API-layer models, not domain use case models


class StartExtractAssembleRequest(BaseModel):
    """Request model for starting extract-assemble workflow."""

    document_id: str = Field(..., min_length=1, description="Document ID to process")
    assembly_specification_id: str = Field(
        ..., min_length=1, description="Assembly specification ID to use"
    )
    workflow_id: str | None = Field(
        None,
        min_length=1,
        description="Optional custom workflow ID (auto-generated if not provided)",
    )


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""

    workflow_id: str
    run_id: str
    status: str
    current_step: str | None = None
    assembly_id: str | None = None


class StartWorkflowResponse(BaseModel):
    """Response model for starting a workflow."""

    workflow_id: str
    run_id: str
    status: str
    message: str


# Dependency placeholder - to be provided by composition layer
async def get_temporal_client() -> Client:
    """Temporal client dependency - override in composition layer."""
    raise NotImplementedError(
        "get_temporal_client must be overridden via dependency_overrides"
    )


@router.post("/extract-assemble", response_model=StartWorkflowResponse)
async def start_extract_assemble_workflow(
    request: StartExtractAssembleRequest,
    temporal_client: Client = Depends(get_temporal_client),
) -> StartWorkflowResponse:
    """Start an extract-assemble workflow."""
    try:
        logger.info("Starting extract-assemble workflow request received")

        workflow_id = request.workflow_id
        if not workflow_id:
            workflow_id = (
                f"extract-assemble-{request.document_id}-"
                f"{request.assembly_specification_id}-{uuid.uuid4().hex[:8]}"
            )

        logger.info(
            "Starting ExtractAssemble workflow",
            extra={
                "workflow_id": workflow_id,
                "document_id": request.document_id,
                "assembly_specification_id": request.assembly_specification_id,
            },
        )

        # Pipeline now takes a dict request (doctrine-compliant pattern)
        # Note: execution_id is injected by TemporalExecutionService, not the request
        pipeline_request = {
            "document_id": request.document_id,
            "assembly_specification_id": request.assembly_specification_id,
        }
        handle = await temporal_client.start_workflow(
            ExtractAssemblePipeline.run,
            args=[pipeline_request],
            id=workflow_id,
            task_queue=CEAP_TASK_QUEUE,
            retry_policy=EXTRACT_ASSEMBLE_RETRY_POLICY,
        )

        logger.info(
            "ExtractAssemble workflow started successfully",
            extra={
                "workflow_id": workflow_id,
                "run_id": handle.run_id,
            },
        )

        return StartWorkflowResponse(
            workflow_id=workflow_id,
            run_id=handle.run_id or "unknown",
            status="RUNNING",
            message="Workflow started successfully",
        )

    except Exception as e:
        logger.error(
            "Failed to start extract-assemble workflow: %s",
            e,
            extra={
                "document_id": request.document_id,
                "assembly_specification_id": request.assembly_specification_id,
            },
        )
        raise HTTPException(status_code=500, detail="Failed to start workflow") from e


@router.get("/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    temporal_client: Client = Depends(get_temporal_client),
) -> WorkflowStatusResponse:
    """Get the status of a workflow."""
    logger.info("Getting workflow status", extra={"workflow_id": workflow_id})

    try:
        handle = temporal_client.get_workflow_handle(workflow_id)
    except Exception as e:
        error_message = str(e).lower()
        if any(
            pattern in error_message
            for pattern in [
                "not found",
                "notfound",
                "does not exist",
                "workflow_not_found",
            ]
        ):
            raise HTTPException(
                status_code=404,
                detail=f"Workflow with ID '{workflow_id}' not found",
            )

        logger.error(
            "Failed to get workflow handle: %s",
            e,
            extra={"workflow_id": workflow_id},
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve workflow handle"
        ) from e

    try:
        description = await handle.describe()
    except Exception as e:
        logger.error(
            "Failed to describe workflow: %s",
            e,
            extra={"workflow_id": workflow_id},
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve workflow description"
        ) from e

    current_step = None
    assembly_id = None
    try:
        current_step = await handle.query("get_current_step")
        assembly_id = await handle.query("get_assembly_id")
    except Exception as query_error:
        logger.debug(
            "Could not query workflow details: %s",
            query_error,
            extra={"workflow_id": workflow_id},
        )

    status_response = WorkflowStatusResponse(
        workflow_id=workflow_id,
        run_id=description.run_id or "unknown",
        status=description.status.name if description.status else "UNKNOWN",
        current_step=current_step,
        assembly_id=assembly_id,
    )

    logger.info(
        "Retrieved workflow status",
        extra={
            "workflow_id": workflow_id,
            "status": status_response.status,
            "current_step": current_step,
        },
    )

    return status_response
