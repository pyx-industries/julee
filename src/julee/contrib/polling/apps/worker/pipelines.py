"""
Doctrine-compliant Temporal workflows for polling operations.

This module contains the refactored pipelines that follow the Pipeline doctrine:
- Pipeline wraps exactly one business UseCase
- run() is the single entry point with @workflow.run
- run_next() handles routing (no decorator)
- Business logic stays in UseCase, not Pipeline

See: docs/architecture/proposals/pipeline_router_design.md
"""

import asyncio
import logging
from typing import Any

from temporalio import workflow

from julee.contrib.polling.domain.use_cases import (
    NewDataDetectionRequest,
    NewDataDetectionResponse,
    NewDataDetectionUseCase,
)
from julee.contrib.polling.infrastructure.temporal.proxies import (
    WorkflowPollerServiceProxy,
)
from julee.shared.entities.pipeline_dispatch import PipelineDispatchItem
from julee.shared.infrastructure.pipeline_routing import (
    RegistryPipelineRequestTransformer,
    pipeline_routing_registry,
)
from julee.shared.use_cases.pipeline_route_response import (
    PipelineRouteResponseRequest,
    PipelineRouteResponseUseCase,
)

logger = logging.getLogger(__name__)


@workflow.defn
class NewDataDetectionPipeline:
    """
    Doctrine-compliant pipeline for endpoint polling with new data detection.

    This pipeline wraps NewDataDetectionUseCase and provides:
    1. Temporal durability guarantees
    2. Routing to downstream pipelines via run_next()
    3. Full dispatch traceability in response

    The pipeline is thin - business logic is in NewDataDetectionUseCase.
    """

    def __init__(self) -> None:
        self.current_step = "initialized"
        self.endpoint_id: str | None = None
        self.has_new_data: bool = False

    @workflow.query
    def get_current_step(self) -> str:
        """Query method to get the current workflow step."""
        return self.current_step

    @workflow.query
    def get_endpoint_id(self) -> str | None:
        """Query method to get the endpoint ID being polled."""
        return self.endpoint_id

    @workflow.query
    def get_has_new_data(self) -> bool:
        """Query method to check if new data was detected."""
        return self.has_new_data

    @workflow.run
    async def run(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the new data detection pipeline.

        Args:
            request: Serialized NewDataDetectionRequest (dict from Temporal)

        Returns:
            Serialized NewDataDetectionResponse with dispatches
        """
        self.current_step = "validating_request"

        # Convert dict to Request (Temporal serializes as dict)
        detection_request = NewDataDetectionRequest.model_validate(request)
        self.endpoint_id = detection_request.endpoint_identifier

        # Check for previous completion result from Temporal schedule
        previous_completion = workflow.get_last_completion_result()
        if previous_completion and "content_hash" in previous_completion:
            detection_request = detection_request.model_copy(
                update={"previous_hash": previous_completion["content_hash"]}
            )

        workflow.logger.info(
            "Starting new data detection pipeline",
            extra={
                "endpoint_id": self.endpoint_id,
                "has_previous_hash": detection_request.previous_hash is not None,
            },
        )

        self.current_step = "executing_use_case"

        # Execute business UseCase
        use_case = NewDataDetectionUseCase(
            poller_service=WorkflowPollerServiceProxy(),
        )
        response = await use_case.execute(detection_request)

        self.has_new_data = response.has_new_data
        self.current_step = "routing"

        # Route to downstream pipelines
        dispatches = await self.run_next(response)
        response.dispatches = dispatches

        self.current_step = "completed"

        workflow.logger.info(
            "New data detection pipeline completed",
            extra={
                "endpoint_id": self.endpoint_id,
                "has_new_data": response.has_new_data,
                "dispatch_count": len(dispatches),
            },
        )

        # Return serialized response for Temporal schedule
        return response.model_dump()

    async def run_next(
        self, response: NewDataDetectionResponse
    ) -> list[PipelineDispatchItem]:
        """
        Route response to downstream pipelines.

        Uses the global routing_registry to find matching routes and
        dispatch child workflows. Solution developers configure routes
        and transformers at startup.

        Args:
            response: The response from the UseCase

        Returns:
            List of PipelineDispatchItem records tracking what was dispatched

        Note: This method does NOT have @workflow.run - it's a helper method.
        """
        # Get routing configuration from global registry
        # (configured by solution developer at startup)
        route_repository = pipeline_routing_registry.get_route_repository()
        request_transformer = RegistryPipelineRequestTransformer(
            pipeline_routing_registry
        )

        # Use PipelineRouteResponseUseCase to find matching routes and transform requests
        routing_use_case = PipelineRouteResponseUseCase(
            route_repository=route_repository,
            request_transformer=request_transformer,
        )

        routing_result = await routing_use_case.execute(
            PipelineRouteResponseRequest(
                response=response.model_dump(),
                response_type=response.__class__.__name__,
            )
        )

        # If no routes matched, return early
        if not routing_result.dispatches:
            workflow.logger.debug(
                "No routes matched for response",
                extra={
                    "response_type": response.__class__.__name__,
                    "endpoint_id": self.endpoint_id,
                },
            )
            return []

        workflow.logger.info(
            "Dispatching to downstream pipelines",
            extra={
                "dispatch_count": len(routing_result.dispatches),
                "pipelines": [d.pipeline for d in routing_result.dispatches],
            },
        )

        # Execute child workflows in parallel
        child_tasks = [
            workflow.execute_child_workflow(
                dispatch.pipeline,
                args=[dispatch.request],
                id=f"{dispatch.pipeline}-{self.endpoint_id}-{workflow.uuid4()}",
            )
            for dispatch in routing_result.dispatches
        ]

        child_responses = await asyncio.gather(*child_tasks, return_exceptions=True)

        # Record results as PipelineDispatchItem
        results = []
        for dispatch, child_response in zip(
            routing_result.dispatches, child_responses, strict=True
        ):
            if isinstance(child_response, Exception):
                results.append(
                    PipelineDispatchItem(
                        pipeline=dispatch.pipeline,
                        request=dispatch.request,
                        response=None,
                        error=f"{type(child_response).__name__}: {child_response}",
                    )
                )
                workflow.logger.error(
                    "Child workflow failed",
                    extra={
                        "pipeline": dispatch.pipeline,
                        "error": str(child_response),
                    },
                )
            else:
                results.append(
                    PipelineDispatchItem(
                        pipeline=dispatch.pipeline,
                        request=dispatch.request,
                        response=child_response,
                        error=None,
                    )
                )

        return results


# Export the pipeline
__all__ = [
    "NewDataDetectionPipeline",
]
