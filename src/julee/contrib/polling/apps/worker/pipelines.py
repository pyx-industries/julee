"""
Temporal workflows for polling operations in the Julee polling contrib module.

This module contains workflows that orchestrate polling operations with
Temporal's durability guarantees, providing retry logic, state management,
and reliable execution for endpoint polling and change detection.
"""

import logging
from typing import Any

from temporalio import workflow

from julee.contrib.polling.domain.models.polling_config import PollingConfig
from julee.contrib.polling.domain.services.polling_result_handler import (
    PollingResultHandler,
)
from julee.contrib.polling.infrastructure.temporal.proxies import (
    WorkflowPollerServiceProxy,
)
from julee.contrib.polling.use_cases.poll_data import PollDataRequest, PollDataUseCase

logger = logging.getLogger(__name__)


@workflow.defn
class NewDataDetectionPipeline:
    """
    Temporal workflow for endpoint polling with new data detection.

    This workflow:
    1. Polls an endpoint using the configured polling service
    2. Compares result with previous completion to detect changes
    3. Hands off to result handler when new data is detected
    4. Returns completion result for next scheduled execution

    The workflow uses Temporal's schedule last completion result feature
    to automatically receive the previous execution's result for comparison.

    Subclasses override get_handler() to supply the appropriate handler
    for each polling use case (credential, product, etc.).
    """

    def __init__(self) -> None:
        self.current_step = "initialized"
        self.endpoint_id: str | None = None
        self.has_new_data: bool = False

    def get_handler(self) -> PollingResultHandler | None:
        """
        Return the PollingResultHandler for this pipeline.

        Subclasses override this method to provide a handler.
        The base implementation returns None (detect only, no handoff).
        """
        return None

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
    async def run(
        self,
        config: PollingConfig | dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute the new data detection workflow.

        Args:
            config: Configuration for the polling operation (PollingConfig or dict
                    from Temporal schedule serialisation)

        Returns:
            Completion result containing polling result and detection metadata

        Raises:
            RuntimeError: If polling fails after retries
        """
        # Convert dict to PollingConfig if needed (Temporal schedules serialise args as dicts)
        if isinstance(config, dict):
            config = PollingConfig.model_validate(config)

        self.endpoint_id = config.endpoint_identifier

        previous_completion = workflow.get_last_completion_result()

        workflow.logger.info(
            "Starting new data detection pipeline",
            extra={
                "endpoint_id": self.endpoint_id,
                "polling_protocol": config.polling_protocol.value,
                "has_previous_completion": previous_completion is not None,
                "workflow_id": workflow.info().workflow_id,
                "run_id": workflow.info().run_id,
            },
        )

        self.current_step = "polling_endpoint"

        try:
            request = PollDataRequest(
                config=config,
                previous_completion=previous_completion,
            )
            use_case = PollDataUseCase(
                poller=WorkflowPollerServiceProxy(),
                handler=self.get_handler(),
            )
            result = await use_case.execute(request)

            self.endpoint_id = result.get("endpoint_id", self.endpoint_id)
            self.has_new_data = result.get("detection_result", {}).get(
                "has_new_data", False
            )
            self.current_step = "completed"

            result["completed_at"] = workflow.now().isoformat()

            workflow.logger.info(
                "New data detection pipeline completed successfully",
                extra={
                    "endpoint_id": self.endpoint_id,
                    "has_new_data": self.has_new_data,
                },
            )

            return result

        except Exception as e:
            self.current_step = "failed"

            workflow.logger.error(
                "New data detection pipeline failed",
                extra={
                    "endpoint_id": self.endpoint_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "current_step": self.current_step,
                },
                exc_info=True,
            )

            raise
