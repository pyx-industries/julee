"""
Unit tests for PollingManager.

This module tests the PollingManager class using mocked Temporal client,
as the test environment doesn't support schedule operations. We mock the
Temporal client to test the manager's business logic and error handling
without requiring actual Temporal infrastructure.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from temporalio.client import Client

from julee.contrib.polling.domain.models.polling_config import (
    PollingConfig,
    PollingProtocol,
)
from julee.contrib.polling.infrastructure.temporal.manager import PollingManager


@pytest.fixture
def mock_temporal_client():
    """Provide a mocked Temporal client."""
    client = AsyncMock(spec=Client)

    # Mock schedule handle for operations with stateful pause behavior
    mock_schedule_handle = AsyncMock()
    client.get_schedule_handle.return_value = mock_schedule_handle

    # Create a stateful mock for pause/resume behavior
    paused_state = {"paused": False}

    async def mock_pause():
        paused_state["paused"] = True

    async def mock_unpause():
        paused_state["paused"] = False

    def mock_describe():
        mock_description = MagicMock()
        mock_description.schedule.state.paused = paused_state["paused"]
        return mock_description

    mock_schedule_handle.pause.side_effect = mock_pause
    mock_schedule_handle.unpause.side_effect = mock_unpause
    mock_schedule_handle.describe.side_effect = mock_describe

    return client


@pytest.fixture
def polling_manager(mock_temporal_client):
    """Provide a PollingManager with mocked client."""
    return PollingManager(mock_temporal_client)


@pytest.fixture
def sample_config():
    """Provide a sample PollingConfig for testing."""
    return PollingConfig(
        endpoint_identifier="test-api",
        polling_protocol=PollingProtocol.HTTP,
        connection_params={"url": "https://api.example.com/data"},
        timeout_seconds=30,
    )


class TestPollingManagerInitialization:
    """Test PollingManager initialization."""

    def test_init_with_client(self, mock_temporal_client):
        """Test initialization with temporal client."""
        manager = PollingManager(mock_temporal_client)
        assert manager._temporal_client is not None
        assert manager._active_polls == {}

    def test_init_without_client(self):
        """Test initialization without temporal client."""
        manager = PollingManager()
        assert manager._temporal_client is None
        assert manager._active_polls == {}

    def test_init_with_custom_task_queue(self, mock_temporal_client):
        """Test initialization with custom task queue."""
        custom_queue = "custom-task-queue"
        manager = PollingManager(mock_temporal_client, task_queue=custom_queue)
        assert manager._temporal_client is not None
        assert manager._task_queue == custom_queue
        assert manager._active_polls == {}

    def test_init_with_default_task_queue(self, mock_temporal_client):
        """Test initialization with default task queue."""
        manager = PollingManager(mock_temporal_client)
        assert manager._temporal_client is not None
        assert manager._task_queue == "julee-polling-queue"
        assert manager._active_polls == {}

    @pytest.mark.asyncio
    async def test_start_polling_with_custom_task_queue(
        self, mock_temporal_client, sample_config
    ):
        """Test that custom task queue is used in schedule creation."""
        custom_queue = "custom-polling-queue"
        manager = PollingManager(mock_temporal_client, task_queue=custom_queue)

        # Capture the schedule created
        schedule_id = await manager.start_polling("test-endpoint", sample_config, 60)

        # Verify create_schedule was called
        mock_temporal_client.create_schedule.assert_called_once()
        call_args = mock_temporal_client.create_schedule.call_args

        # Verify the schedule uses the custom task queue
        schedule_obj = call_args[1]["schedule"]  # kwargs['schedule']
        assert schedule_obj.action.task_queue == custom_queue
        assert schedule_id == "poll-test-endpoint"


class TestPollingManagerStartPolling:
    """Test PollingManager start_polling method."""

    @pytest.mark.asyncio
    async def test_start_polling_success(self, polling_manager, sample_config):
        """Test successful polling start creates schedule and tracks state."""
        schedule_id = await polling_manager.start_polling(
            "test-endpoint", sample_config, 60
        )

        # Verify return value
        assert schedule_id == "poll-test-endpoint"

        # Verify internal tracking
        assert "test-endpoint" in polling_manager._active_polls
        poll_info = polling_manager._active_polls["test-endpoint"]
        assert poll_info["schedule_id"] == "poll-test-endpoint"
        assert poll_info["config"] == sample_config
        assert poll_info["interval_seconds"] == 60
        assert poll_info["downstream_pipeline"] is None

    @pytest.mark.asyncio
    async def test_start_polling_with_downstream_pipeline(
        self, polling_manager, sample_config
    ):
        """Test polling start with downstream pipeline."""
        schedule_id = await polling_manager.start_polling(
            "test-endpoint", sample_config, 30, "custom-pipeline"
        )

        assert schedule_id == "poll-test-endpoint"
        poll_info = polling_manager._active_polls["test-endpoint"]
        assert poll_info["downstream_pipeline"] == "custom-pipeline"

    @pytest.mark.asyncio
    async def test_start_polling_duplicate_endpoint_raises_error(
        self, polling_manager, sample_config
    ):
        """Test starting polling for duplicate endpoint raises ValueError."""
        # Start polling first time
        await polling_manager.start_polling("test-endpoint", sample_config, 60)

        # Attempt to start again should raise error
        with pytest.raises(
            ValueError, match="Endpoint test-endpoint is already being polled"
        ):
            await polling_manager.start_polling("test-endpoint", sample_config, 60)

    @pytest.mark.asyncio
    async def test_start_polling_no_client_raises_error(self, sample_config):
        """Test starting polling without client raises RuntimeError."""
        manager = PollingManager()  # No client

        with pytest.raises(RuntimeError, match="Temporal client not available"):
            await manager.start_polling("test-endpoint", sample_config, 60)

    @pytest.mark.asyncio
    async def test_start_polling_multiple_endpoints(
        self, polling_manager, sample_config
    ):
        """Test starting polling for multiple endpoints."""
        # Create different configs for different endpoints
        config2 = PollingConfig(
            endpoint_identifier="test-api-2",
            polling_protocol=PollingProtocol.HTTP,
            connection_params={"url": "https://api2.example.com/data"},
        )

        # Start polling for multiple endpoints
        schedule_id1 = await polling_manager.start_polling(
            "endpoint-1", sample_config, 60
        )
        schedule_id2 = await polling_manager.start_polling("endpoint-2", config2, 30)

        # Verify both are tracked
        assert schedule_id1 == "poll-endpoint-1"
        assert schedule_id2 == "poll-endpoint-2"
        assert "endpoint-1" in polling_manager._active_polls
        assert "endpoint-2" in polling_manager._active_polls
        assert len(polling_manager._active_polls) == 2


class TestPollingManagerStopPolling:
    """Test PollingManager stop_polling method."""

    @pytest.mark.asyncio
    async def test_stop_polling_success(self, polling_manager, sample_config):
        """Test successful polling stop removes schedule and tracking."""
        # Start polling first
        await polling_manager.start_polling("test-endpoint", sample_config, 60)
        assert "test-endpoint" in polling_manager._active_polls

        # Stop polling
        result = await polling_manager.stop_polling("test-endpoint")

        # Verify success and cleanup
        assert result is True
        assert "test-endpoint" not in polling_manager._active_polls

    @pytest.mark.asyncio
    async def test_stop_polling_nonexistent_endpoint(self, polling_manager):
        """Test stopping polling for non-existent endpoint returns False."""
        result = await polling_manager.stop_polling("nonexistent-endpoint")
        assert result is False

    @pytest.mark.asyncio
    async def test_stop_polling_no_client_raises_error(self, sample_config):
        """Test stopping polling without client raises RuntimeError."""
        manager = PollingManager()  # No client
        # Manually add to tracking to test the error condition
        manager._active_polls["test-endpoint"] = {
            "schedule_id": "poll-test-endpoint",
            "config": sample_config,
            "interval_seconds": 60,
            "downstream_pipeline": None,
        }

        with pytest.raises(RuntimeError, match="Temporal client not available"):
            await manager.stop_polling("test-endpoint")


class TestPollingManagerListActivePolling:
    """Test PollingManager list_active_polling method."""

    @pytest.mark.asyncio
    async def test_list_active_polling_empty(self, polling_manager):
        """Test listing active polls when none exist."""
        active_polls = await polling_manager.list_active_polling()
        assert active_polls == []

    @pytest.mark.asyncio
    async def test_list_active_polling_with_data(self, polling_manager, sample_config):
        """Test listing active polls with existing data."""
        # Start some polling operations
        await polling_manager.start_polling("endpoint-1", sample_config, 60)
        await polling_manager.start_polling(
            "endpoint-2", sample_config, 30, "pipeline-2"
        )

        # List active polling
        active_polls = await polling_manager.list_active_polling()

        # Verify results
        assert len(active_polls) == 2

        # Find polls by endpoint_id (order not guaranteed)
        endpoint1_poll = next(
            p for p in active_polls if p["endpoint_id"] == "endpoint-1"
        )
        endpoint2_poll = next(
            p for p in active_polls if p["endpoint_id"] == "endpoint-2"
        )

        # Verify endpoint-1 details
        assert endpoint1_poll["schedule_id"] == "poll-endpoint-1"
        assert endpoint1_poll["interval_seconds"] == 60
        assert endpoint1_poll["endpoint_identifier"] == "test-api"
        assert endpoint1_poll["polling_protocol"] == "http"
        assert endpoint1_poll["downstream_pipeline"] is None

        # Verify endpoint-2 details
        assert endpoint2_poll["schedule_id"] == "poll-endpoint-2"
        assert endpoint2_poll["interval_seconds"] == 30
        assert endpoint2_poll["downstream_pipeline"] == "pipeline-2"


class TestPollingManagerGetPollingStatus:
    """Test PollingManager get_polling_status method."""

    @pytest.mark.asyncio
    async def test_get_polling_status_nonexistent_endpoint(self, polling_manager):
        """Test getting status for non-existent endpoint returns None."""
        status = await polling_manager.get_polling_status("nonexistent-endpoint")
        assert status is None

    @pytest.mark.asyncio
    async def test_get_polling_status_no_client_raises_error(self, sample_config):
        """Test getting status without client raises RuntimeError."""
        manager = PollingManager()  # No client
        # Manually add to tracking to test the error condition
        manager._active_polls["test-endpoint"] = {
            "schedule_id": "poll-test-endpoint",
            "config": sample_config,
            "interval_seconds": 60,
            "downstream_pipeline": None,
        }

        with pytest.raises(RuntimeError, match="Temporal client not available"):
            await manager.get_polling_status("test-endpoint")

    @pytest.mark.asyncio
    async def test_get_polling_status_success(self, polling_manager, sample_config):
        """Test getting status for existing endpoint."""
        # Start polling
        await polling_manager.start_polling(
            "test-endpoint", sample_config, 60, "test-pipeline"
        )

        # Get status
        status = await polling_manager.get_polling_status("test-endpoint")

        # Verify status details
        assert status is not None
        assert status["endpoint_id"] == "test-endpoint"
        assert status["schedule_id"] == "poll-test-endpoint"
        assert status["interval_seconds"] == 60
        assert status["downstream_pipeline"] == "test-pipeline"
        # Should not be paused initially
        assert status["is_paused"] is False


class TestPollingManagerPauseResumePolling:
    """Test PollingManager pause_polling and resume_polling methods."""

    @pytest.mark.asyncio
    async def test_pause_polling_success(self, polling_manager, sample_config):
        """Test successful polling pause."""
        # Start polling
        await polling_manager.start_polling("test-endpoint", sample_config, 60)

        # Pause polling
        result = await polling_manager.pause_polling("test-endpoint")
        assert result is True

    @pytest.mark.asyncio
    async def test_pause_polling_nonexistent_endpoint(self, polling_manager):
        """Test pausing non-existent endpoint returns False."""
        result = await polling_manager.pause_polling("nonexistent-endpoint")
        assert result is False

    @pytest.mark.asyncio
    async def test_pause_polling_no_client_raises_error(self, sample_config):
        """Test pausing polling without client raises RuntimeError."""
        manager = PollingManager()  # No client
        # Manually add to tracking to test the error condition
        manager._active_polls["test-endpoint"] = {
            "schedule_id": "poll-test-endpoint",
            "config": sample_config,
            "interval_seconds": 60,
            "downstream_pipeline": None,
        }

        with pytest.raises(RuntimeError, match="Temporal client not available"):
            await manager.pause_polling("test-endpoint")

    @pytest.mark.asyncio
    async def test_resume_polling_success(self, polling_manager, sample_config):
        """Test successful polling resume."""
        # Start and pause polling
        await polling_manager.start_polling("test-endpoint", sample_config, 60)
        await polling_manager.pause_polling("test-endpoint")

        # Resume polling
        result = await polling_manager.resume_polling("test-endpoint")
        assert result is True

    @pytest.mark.asyncio
    async def test_resume_polling_nonexistent_endpoint(self, polling_manager):
        """Test resuming non-existent endpoint returns False."""
        result = await polling_manager.resume_polling("nonexistent-endpoint")
        assert result is False

    @pytest.mark.asyncio
    async def test_resume_polling_no_client_raises_error(self, sample_config):
        """Test resuming polling without client raises RuntimeError."""
        manager = PollingManager()  # No client
        # Manually add to tracking to test the error condition
        manager._active_polls["test-endpoint"] = {
            "schedule_id": "poll-test-endpoint",
            "config": sample_config,
            "interval_seconds": 60,
            "downstream_pipeline": None,
        }

        with pytest.raises(RuntimeError, match="Temporal client not available"):
            await manager.resume_polling("test-endpoint")

    @pytest.mark.asyncio
    async def test_pause_resume_workflow(self, polling_manager, sample_config):
        """Test complete pause/resume workflow."""
        # Start polling
        await polling_manager.start_polling("test-endpoint", sample_config, 60)

        # Pause polling
        await polling_manager.pause_polling("test-endpoint")

        # Verify paused status
        status = await polling_manager.get_polling_status("test-endpoint")
        assert status["is_paused"] is True

        # Resume polling
        await polling_manager.resume_polling("test-endpoint")

        # Verify resumed status
        status = await polling_manager.get_polling_status("test-endpoint")
        assert status["is_paused"] is False


class TestPollingManagerIntegration:
    """Integration tests for PollingManager full workflows."""

    @pytest.mark.asyncio
    async def test_full_polling_lifecycle(self, polling_manager, sample_config):
        """Test complete polling lifecycle: start -> pause -> resume -> stop."""
        endpoint_id = "lifecycle-test"

        # Start polling
        schedule_id = await polling_manager.start_polling(
            endpoint_id, sample_config, 45
        )
        assert schedule_id == f"poll-{endpoint_id}"

        # Verify it's in active polls
        active_polls = await polling_manager.list_active_polling()
        assert len(active_polls) == 1
        assert active_polls[0]["endpoint_id"] == endpoint_id

        # Pause polling
        assert await polling_manager.pause_polling(endpoint_id) is True
        status = await polling_manager.get_polling_status(endpoint_id)
        assert status["is_paused"] is True

        # Resume polling
        assert await polling_manager.resume_polling(endpoint_id) is True
        status = await polling_manager.get_polling_status(endpoint_id)
        assert status["is_paused"] is False

        # Stop polling
        assert await polling_manager.stop_polling(endpoint_id) is True

        # Verify cleanup
        assert await polling_manager.get_polling_status(endpoint_id) is None
        active_polls = await polling_manager.list_active_polling()
        assert len(active_polls) == 0
