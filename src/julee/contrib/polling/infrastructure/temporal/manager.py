"""
PollingManager for high-level HTTP endpoint polling operations.

This module provides a simple, framework-agnostic API for managing
HTTP endpoint polling with automatic change detection and pipeline
triggering. It abstracts away the underlying Temporal scheduling
implementation.
"""

import logging
from datetime import timedelta
from typing import Any

from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleAlreadyRunningError,
    ScheduleIntervalSpec,
    ScheduleOverlapPolicy,
    SchedulePolicy,
    ScheduleSpec,
    ScheduleUpdate,
    ScheduleUpdateInput,
)

from julee.contrib.polling.domain.models.polling_config import (
    PollingConfig,
    SchedulingPolicy,
)

logger = logging.getLogger(__name__)


class PollingManager:
    """
    High-level manager for HTTP endpoint polling operations.

    This class provides a simple API for starting and stopping polling
    operations using Temporal schedules for reliable execution. Users
    must provide a Temporal client during initialization, following the
    same pattern as other Julee infrastructure components.

    The manager handles:
    - Creating and managing Temporal schedules for polling
    - Tracking active polling operations
    - Providing status and control operations (pause/resume/stop)

    Example:
        # Using default task queue
        manager = PollingManager(temporal_client)

        # Using custom task queue
        manager = PollingManager(temporal_client, task_queue="my-polling-queue")
    """

    def __init__(
        self,
        temporal_client: Client | None = None,
        task_queue: str = "julee-polling-queue",
    ) -> None:
        """
        Initialize the polling manager.

        Args:
            temporal_client: Temporal client for schedule management.
                           Typically created at application startup level
                           (worker, API) and passed to the manager.
            task_queue: Task queue name for workflow execution.
                       Defaults to "julee-polling-queue".
        """
        self._temporal_client = temporal_client
        self._task_queue = task_queue
        self._active_polls: dict[str, dict[str, Any]] = {}

    async def start_polling(
        self,
        endpoint_id: str,
        config: PollingConfig,
        interval_seconds: int,
        workflow_name: str = "NewDataDetectionPipeline",
    ) -> str:
        """
        Start polling an HTTP endpoint at regular intervals.

        Args:
            endpoint_id: Unique identifier for this polling operation
            config: Configuration for the polling operation
            interval_seconds: How often to poll (in seconds)
            workflow_name: Name of the Temporal workflow to schedule.
                           Defaults to "NewDataDetectionPipeline"; override
                           to use a subclass registered under a different name.

        Returns:
            Schedule ID that was created

        Raises:
            ValueError: If endpoint_id is already being polled
            RuntimeError: If Temporal client is not available
        """
        if endpoint_id in self._active_polls:
            raise ValueError(f"Endpoint {endpoint_id} is already being polled")

        if self._temporal_client is None:
            raise RuntimeError("Temporal client not available")

        schedule_id = f"poll-{endpoint_id}"

        # Map Julee scheduling policy to Temporal overlap policy
        temporal_overlap_policy = (
            ScheduleOverlapPolicy.SKIP
            if config.scheduling_policy == SchedulingPolicy.SKIP_IF_RUNNING
            else ScheduleOverlapPolicy.ALLOW_ALL
        )

        schedule = Schedule(
            action=ScheduleActionStartWorkflow(
                workflow_name,
                args=[config],
                id=f"{schedule_id}-{{.timestamp}}",
                task_queue=self._task_queue,
            ),
            spec=ScheduleSpec(
                intervals=[
                    ScheduleIntervalSpec(every=timedelta(seconds=interval_seconds))
                ]
            ),
            policy=SchedulePolicy(overlap=temporal_overlap_policy),
        )

        try:
            await self._temporal_client.create_schedule(
                id=schedule_id, schedule=schedule
            )
            logger.info(
                f"Created new schedule {schedule_id} for endpoint {endpoint_id}"
            )
        except ScheduleAlreadyRunningError:
            # Update existing schedule preserving history
            logger.info(f"Updating existing schedule {schedule_id}")
            schedule_handle = self._temporal_client.get_schedule_handle(schedule_id)

            # Create update function that modifies the schedule
            async def update_schedule_callback(
                input: ScheduleUpdateInput,
            ) -> ScheduleUpdate:
                # Update the schedule with new configuration
                updated_schedule = input.description.schedule
                updated_schedule.action = schedule.action
                updated_schedule.spec = schedule.spec
                return ScheduleUpdate(schedule=updated_schedule)

            await schedule_handle.update(update_schedule_callback)
            logger.info(f"Updated schedule {schedule_id} for endpoint {endpoint_id}")

        # Track the active polling operation
        self._active_polls[endpoint_id] = {
            "schedule_id": schedule_id,
            "config": config,
            "interval_seconds": interval_seconds,
            "workflow_name": workflow_name,
        }

        return schedule_id

    async def stop_polling(self, endpoint_id: str) -> bool:
        """
        Stop polling an endpoint.

        Args:
            endpoint_id: The endpoint ID to stop polling

        Returns:
            True if polling was stopped, False if not found

        Raises:
            RuntimeError: If Temporal client is not available
        """
        if endpoint_id not in self._active_polls:
            return False

        if self._temporal_client is None:
            raise RuntimeError("Temporal client not available")

        poll_info = self._active_polls[endpoint_id]
        schedule_id = poll_info["schedule_id"]

        # Delete the Temporal schedule
        schedule_handle = self._temporal_client.get_schedule_handle(schedule_id)
        await schedule_handle.delete()

        # Remove from tracking
        del self._active_polls[endpoint_id]

        return True

    async def list_active_polling(self) -> list[dict[str, Any]]:
        """
        List all active polling operations.

        Returns:
            List of dictionaries containing polling operation details
        """
        active_polls = []

        for endpoint_id, poll_info in self._active_polls.items():
            active_polls.append(
                {
                    "endpoint_id": endpoint_id,
                    "schedule_id": poll_info["schedule_id"],
                    "interval_seconds": poll_info["interval_seconds"],
                    "endpoint_identifier": poll_info["config"].endpoint_identifier,
                    "polling_protocol": poll_info["config"].polling_protocol.value,
                    "workflow_name": poll_info.get("workflow_name"),
                }
            )

        return active_polls

    async def get_polling_status(self, endpoint_id: str) -> dict[str, Any] | None:
        """
        Get the status of a specific polling operation.

        Args:
            endpoint_id: The endpoint ID to check

        Returns:
            Dictionary with status information or None if not found

        Raises:
            RuntimeError: If Temporal client is not available
        """
        if endpoint_id not in self._active_polls:
            return None

        if self._temporal_client is None:
            raise RuntimeError("Temporal client not available")

        poll_info = self._active_polls[endpoint_id]
        schedule_id = poll_info["schedule_id"]

        # Get schedule information from Temporal
        schedule_handle = self._temporal_client.get_schedule_handle(schedule_id)
        schedule_description = await schedule_handle.describe()

        return {
            "endpoint_id": endpoint_id,
            "schedule_id": schedule_id,
            "interval_seconds": poll_info["interval_seconds"],
            "is_paused": schedule_description.schedule.state.paused,
            "workflow_name": poll_info.get("workflow_name"),
        }

    async def pause_polling(self, endpoint_id: str) -> bool:
        """
        Pause polling for an endpoint (without deleting the schedule).

        Args:
            endpoint_id: The endpoint ID to pause

        Returns:
            True if paused successfully, False if not found

        Raises:
            RuntimeError: If Temporal client is not available
        """
        if endpoint_id not in self._active_polls:
            return False

        if self._temporal_client is None:
            raise RuntimeError("Temporal client not available")

        poll_info = self._active_polls[endpoint_id]
        schedule_id = poll_info["schedule_id"]

        schedule_handle = self._temporal_client.get_schedule_handle(schedule_id)
        await schedule_handle.pause()

        return True

    async def resume_polling(self, endpoint_id: str) -> bool:
        """
        Resume a paused polling operation.

        Args:
            endpoint_id: The endpoint ID to resume

        Returns:
            True if resumed successfully, False if not found

        Raises:
            RuntimeError: If Temporal client is not available
        """
        if endpoint_id not in self._active_polls:
            return False

        if self._temporal_client is None:
            raise RuntimeError("Temporal client not available")

        poll_info = self._active_polls[endpoint_id]
        schedule_id = poll_info["schedule_id"]

        schedule_handle = self._temporal_client.get_schedule_handle(schedule_id)
        await schedule_handle.unpause()

        return True
