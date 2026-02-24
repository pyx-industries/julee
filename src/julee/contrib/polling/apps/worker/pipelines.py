"""
Temporal workflows for polling operations in the Julee polling contrib module.

This module contains workflows that orchestrate polling operations with
Temporal's durability guarantees, providing retry logic, state management,
and reliable execution for endpoint polling and change detection.
"""

import hashlib
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
    """

    def __init__(self, result_handler: PollingResultHandler) -> None:
        self.current_step = "initialized"
        self.endpoint_id: str | None = None
        self.has_new_data: bool = False
        self._result_handler = result_handler

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
            config: Configuration for the polling operation (PollingConfig or dict from schedule)

        Returns:
            Completion result containing polling result and detection metadata

        Raises:
            RuntimeError: If polling fails after retries
        """
        # Convert dict to PollingConfig if needed (for schedule compatibility)
        # Temporal schedules serialize arguments as dicts, not Pydantic models
        if isinstance(config, dict):
            config = PollingConfig.model_validate(config)

        self.endpoint_id = config.endpoint_identifier

        # Fetch previous completion result from Temporal
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
            # Step 1: Poll the endpoint
            polling_service = WorkflowPollerServiceProxy()
            polling_result = await polling_service.poll_endpoint(config)

            # Extract the timestamp from when polling actually happened
            polled_at = polling_result.polled_at.isoformat()

            workflow.logger.debug(
                "Polling completed",
                extra={
                    "endpoint_id": self.endpoint_id,
                    "polling_success": polling_result.success,
                    "content_length": len(polling_result.content),
                },
            )

            self.current_step = "detecting_changes"

            # Step 2: Detect new data using hash comparison
            current_content = polling_result.content
            current_hash = hashlib.sha256(current_content).hexdigest()

            previous_hash = None
            if previous_completion and "polling_result" in previous_completion:
                previous_hash = previous_completion["polling_result"].get(
                    "content_hash"
                )

            has_new_data = previous_hash != current_hash
            self.has_new_data = has_new_data

            workflow.logger.info(
                f"DEBUG: Change detection - has_new_data: {has_new_data}, "
                f"is_first_run: {previous_hash is None}, "
                f"current_hash: {current_hash[:8]}..., "
                f"previous_hash: {previous_hash[:8] if previous_hash else 'None'}..."
            )

            # Step 3: Hand off to result handler if new data detected
            handler_acknowledgement = None
            if has_new_data:
                self.current_step = "handling_new_data"

                workflow.logger.info(
                    "Handing off new data to result handler",
                    extra={
                        "endpoint_id": self.endpoint_id,
                        "content_length": len(current_content),
                    },
                )

                # Get previous data for handler
                previous_data = None
                if previous_completion and "polling_result" in previous_completion:
                    prev_content_str = previous_completion["polling_result"].get(
                        "content"
                    )
                    if prev_content_str:
                        try:
                            previous_data = prev_content_str.encode("utf-8")
                        except (UnicodeDecodeError, AttributeError) as e:
                            workflow.logger.error(
                                "Failed to decode previous content for handler",
                                extra={
                                    "endpoint_id": self.endpoint_id,
                                    "error": str(e),
                                    "error_type": type(e).__name__,
                                },
                            )
                            raise RuntimeError(
                                f"Previous content is corrupted or invalid: {e}"
                            )

                try:
                    handler_acknowledgement = (
                        await self._result_handler.handle_new_data(
                            endpoint_id=self.endpoint_id,
                            previous_data=previous_data,
                            new_data=current_content,
                            content_hash=current_hash,
                        )
                    )

                    # Log handler response
                    workflow.logger.info(
                        f"Handler response: {handler_acknowledgement}",
                        extra={
                            "endpoint_id": self.endpoint_id,
                            "handler_response": str(handler_acknowledgement),
                            "handler_info": handler_acknowledgement.info,
                        },
                    )

                except Exception as e:
                    workflow.logger.error(
                        "Handler failed to process new data",
                        extra={
                            "endpoint_id": self.endpoint_id,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )
                    # Don't fail the polling workflow if handler fails
                    # handler_acknowledgement remains None to indicate handler exception

            self.current_step = "completed"

            # Step 4: Return completion result for next scheduled execution
            completion_result = {
                "polling_result": {
                    "success": polling_result.success,
                    "content_hash": current_hash,
                    "content": current_content.decode("utf-8", errors="ignore"),
                    "polled_at": polled_at,
                    "content_length": len(current_content),
                },
                "detection_result": {
                    "has_new_data": has_new_data,
                    "previous_hash": previous_hash,
                    "current_hash": current_hash,
                },
                "handler_acknowledgement": handler_acknowledgement,
                "endpoint_id": self.endpoint_id,
                "completed_at": workflow.now().isoformat(),
            }

            workflow.logger.info(
                "New data detection pipeline completed successfully",
                extra={
                    "endpoint_id": self.endpoint_id,
                    "has_new_data": has_new_data,
                    "handler_acknowledgement": handler_acknowledgement,
                },
            )

            return completion_result

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

            # Re-raise to let Temporal handle retry logic
            raise
