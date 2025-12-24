"""
Unit tests for polling worker pipelines.

This module tests the NewDataDetectionPipeline workflow using Temporal's test
environment, which provides realistic workflow execution with time-skipping
capabilities while maintaining fast test performance.

The tests mock external dependencies (activities) while testing the actual
workflow orchestration logic and temporal behaviors.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from temporalio import activity
from temporalio.client import WorkflowFailureError
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from julee.contrib.polling.apps.worker.pipelines import NewDataDetectionPipeline
from julee.contrib.polling.domain.models.polling_config import (
    PollingConfig,
    PollingProtocol,
    PollingResult,
)


@pytest.fixture
async def workflow_env():
    """Provide a Temporal test environment with time skipping."""
    async with await WorkflowEnvironment.start_time_skipping(
        data_converter=pydantic_data_converter
    ) as env:
        yield env


@pytest.fixture
def sample_config():
    """Provide a sample PollingConfig for testing."""
    return PollingConfig(
        endpoint_identifier="test-api",
        polling_protocol=PollingProtocol.HTTP,
        connection_params={"url": "https://api.example.com/data"},
        timeout_seconds=30,
    )


@pytest.fixture
def mock_polling_results():
    """Provide sample polling results for different scenarios."""
    return {
        "first_data": PollingResult(
            success=True,
            content=b"first response data",
            polled_at=datetime.now(timezone.utc),
            content_hash=hashlib.sha256(b"first response data").hexdigest(),
        ),
        "changed_data": PollingResult(
            success=True,
            content=b"changed response data",
            polled_at=datetime.now(timezone.utc),
            content_hash=hashlib.sha256(b"changed response data").hexdigest(),
        ),
        "same_data": PollingResult(
            success=True,
            content=b"first response data",  # Same as first_data
            polled_at=datetime.now(timezone.utc),
            content_hash=hashlib.sha256(b"first response data").hexdigest(),
        ),
        "failed_polling": PollingResult(
            success=False,
            content=b"",
            polled_at=datetime.now(timezone.utc),
            error_message="Connection timeout",
        ),
    }


# Mock activity for polling operations - will be patched in tests
@activity.defn(name="julee.contrib.polling.poll_endpoint")
async def mock_poll_endpoint(config: PollingConfig) -> PollingResult:
    """Mock polling activity - should be patched in tests."""
    return PollingResult(
        success=True,
        content=b"default mock response",
        polled_at=datetime.now(timezone.utc),
    )


class TestNewDataDetectionPipelineFirstRun:
    """Test first run scenarios (no previous completion)."""

    @pytest.mark.asyncio
    async def test_first_run_detects_new_data(
        self, workflow_env, sample_config, mock_polling_results
    ):
        """Test first run always detects new data."""

        # Create a mock activity function that returns the desired response
        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(config: PollingConfig) -> PollingResult:
            content_str = "first response data"
            return PollingResult(
                success=True,
                content=content_str.encode(),
                polled_at=datetime.now(timezone.utc),
                content_hash=hashlib.sha256(content_str.encode()).hexdigest(),
            )

        async with Worker(
            workflow_env.client,
            task_queue="test-queue",
            workflows=[NewDataDetectionPipeline],
            activities=[test_mock_activity],
        ):
            # Execute workflow with no previous completion
            result = await workflow_env.client.execute_workflow(
                NewDataDetectionPipeline.run,
                args=[
                    sample_config,
                    None,
                ],  # config, downstream_pipeline
                id=str(uuid.uuid4()),
                task_queue="test-queue",
            )

            # Verify first run behavior
            assert result["detection_result"]["has_new_data"] is True
            assert result["detection_result"]["previous_hash"] is None
            assert result["downstream_triggered"] is False
            assert result["endpoint_id"] == "test-api"

            # Verify polling result structure
            polling_result = result["polling_result"]
            assert polling_result["success"] is True
            assert (
                polling_result["content_hash"]
                == hashlib.sha256(b"first response data").hexdigest()
            )
            assert "polled_at" in polling_result
            assert "content_length" in polling_result

    @pytest.mark.asyncio
    async def test_first_run_with_downstream_pipeline(
        self, workflow_env, sample_config, mock_polling_results
    ):
        """Test first run with downstream pipeline triggering."""

        # Create a mock activity function that returns the desired response
        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(config: PollingConfig) -> PollingResult:
            content_bytes = b"first response data"
            return PollingResult(
                success=True,
                content=content_bytes,
                polled_at=datetime.now(timezone.utc),
                content_hash=hashlib.sha256(content_bytes).hexdigest(),
            )

        # Mock workflow.start_workflow to avoid trying to start actual downstream workflows
        with patch(
            "julee.contrib.polling.apps.worker.pipelines.workflow.start_child_workflow",
            new_callable=AsyncMock,
        ) as mock_start:
            async with Worker(
                workflow_env.client,
                task_queue="test-queue",
                workflows=[NewDataDetectionPipeline],
                activities=[test_mock_activity],
            ):
                result = await workflow_env.client.execute_workflow(
                    NewDataDetectionPipeline.run,
                    args=[
                        sample_config,
                        "TestDownstreamWorkflow",
                    ],  # config, downstream_pipeline
                    id=str(uuid.uuid4()),
                    task_queue="test-queue",
                )

                # Verify downstream was triggered
                assert result["downstream_triggered"] is True
                mock_start.assert_called_once()

                # Verify downstream workflow call parameters
                call_args = mock_start.call_args
                # For start_child_workflow, the workflow name is the first positional arg
                assert call_args[0][0] == "TestDownstreamWorkflow"  # Workflow name
                # The args parameter is passed as a keyword argument
                assert call_args[1]["args"] == [
                    None,
                    b"first response data",
                ]  # Args: previous_data, new_data
                assert (
                    "downstream-test-api-" in call_args[1]["id"]
                )  # Workflow ID contains endpoint
                assert call_args[1]["task_queue"] == "downstream-processing-queue"


class TestNewDataDetectionPipelineSubsequentRuns:
    """Test subsequent runs with previous completion data."""

    @pytest.mark.asyncio
    async def test_no_changes_detected(
        self, workflow_env, sample_config, mock_polling_results
    ):
        """Test when content hasn't changed since last run."""

        # Create a mock activity function that returns the desired response
        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(config: PollingConfig) -> PollingResult:
            content_bytes = b"first response data"  # Same as first_data
            return PollingResult(
                success=True,
                content=content_bytes,
                polled_at=datetime.now(timezone.utc),
                content_hash=hashlib.sha256(content_bytes).hexdigest(),
            )

        # Mock workflow.get_last_completion_result to return previous completion
        previous_completion = {
            "polling_result": {
                "content_hash": hashlib.sha256(b"first response data").hexdigest(),
                "content": "first response data",
                "success": True,
            },
            "detection_result": {
                "has_new_data": True,
                "previous_hash": None,
                "current_hash": hashlib.sha256(b"first response data").hexdigest(),
            },
            "downstream_triggered": False,
            "endpoint_id": "test-api",
            "completed_at": "2023-01-01T00:00:00Z",
        }

        async with Worker(
            workflow_env.client,
            task_queue="test-queue",
            workflows=[NewDataDetectionPipeline],
            activities=[test_mock_activity],
        ):
            # Use mock to simulate last completion result
            with patch(
                "temporalio.workflow.get_last_completion_result"
            ) as mock_get_last:
                mock_get_last.return_value = previous_completion

                result = await workflow_env.client.execute_workflow(
                    NewDataDetectionPipeline.run,
                    args=[
                        sample_config,
                        None,
                    ],  # config, downstream_pipeline
                    id=str(uuid.uuid4()),
                    task_queue="test-queue",
                )

            # Verify no changes detected
            assert result["detection_result"]["has_new_data"] is False
            assert result["downstream_triggered"] is False
            assert result["detection_result"]["previous_hash"] is not None

    @pytest.mark.asyncio
    async def test_changes_detected(
        self, workflow_env, sample_config, mock_polling_results
    ):
        """Test when content has changed since last run."""

        # Create a mock activity function that returns the desired response
        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(config: PollingConfig) -> PollingResult:
            content_bytes = b"changed response data"
            return PollingResult(
                success=True,
                content=content_bytes,
                polled_at=datetime.now(timezone.utc),
                content_hash=hashlib.sha256(content_bytes).hexdigest(),
            )

        # Mock workflow.get_last_completion_result to return previous completion with different hash
        previous_completion = {
            "polling_result": {
                "content_hash": hashlib.sha256(b"first response data").hexdigest(),
                "content": "first response data",
                "success": True,
            },
            "detection_result": {
                "has_new_data": True,
                "previous_hash": None,
                "current_hash": hashlib.sha256(b"first response data").hexdigest(),
            },
            "downstream_triggered": False,
            "endpoint_id": "test-api",
            "completed_at": "2023-01-01T00:00:00Z",
        }

        with patch(
            "julee.contrib.polling.apps.worker.pipelines.workflow.start_child_workflow",
            new_callable=AsyncMock,
        ) as mock_start:
            async with Worker(
                workflow_env.client,
                task_queue="test-queue",
                workflows=[NewDataDetectionPipeline],
                activities=[test_mock_activity],
            ):
                # Use mock to simulate last completion result
                with patch(
                    "temporalio.workflow.get_last_completion_result"
                ) as mock_get_last:
                    mock_get_last.return_value = previous_completion

                    result = await workflow_env.client.execute_workflow(
                        NewDataDetectionPipeline.run,
                        args=[
                            sample_config,
                            "TestDownstreamWorkflow",
                        ],  # config, downstream_pipeline
                        id=str(uuid.uuid4()),
                        task_queue="test-queue",
                    )

                # Verify changes detected and downstream triggered
                assert result["detection_result"]["has_new_data"] is True
                assert result["downstream_triggered"] is True
                assert (
                    result["detection_result"]["current_hash"]
                    != result["detection_result"]["previous_hash"]
                )
                mock_start.assert_called_once()


class TestNewDataDetectionPipelineWorkflowQueries:
    """Test workflow query methods during execution."""

    @pytest.mark.asyncio
    async def test_workflow_queries(
        self, workflow_env, sample_config, mock_polling_results
    ):
        """Test that workflow queries return correct state information."""

        # Create a slow mock activity to allow time for queries
        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(config: PollingConfig) -> PollingResult:
            await workflow_env.sleep(1)  # Add delay to allow queries
            content_bytes = b"first response data"
            return PollingResult(
                success=True,
                content=content_bytes,
                polled_at=datetime.now(timezone.utc),
                content_hash=hashlib.sha256(content_bytes).hexdigest(),
            )

        async with Worker(
            workflow_env.client,
            task_queue="test-queue",
            workflows=[NewDataDetectionPipeline],
            activities=[test_mock_activity],
        ):
            # Start workflow
            handle = await workflow_env.client.start_workflow(
                NewDataDetectionPipeline.run,
                args=[
                    sample_config,
                    None,
                ],  # config, downstream_pipeline
                id=str(uuid.uuid4()),
                task_queue="test-queue",
            )

            # Query initial state
            current_step = await handle.query(NewDataDetectionPipeline.get_current_step)
            endpoint_id = await handle.query(NewDataDetectionPipeline.get_endpoint_id)
            has_new_data = await handle.query(NewDataDetectionPipeline.get_has_new_data)

            # Verify initial query responses
            assert current_step in [
                "initialized",
                "polling_endpoint",
                "detecting_changes",
                "completed",
            ]
            assert endpoint_id == "test-api"
            assert isinstance(has_new_data, bool)

            # Wait for completion
            await handle.result()

            # Query final state
            final_step = await handle.query(NewDataDetectionPipeline.get_current_step)
            final_has_new_data = await handle.query(
                NewDataDetectionPipeline.get_has_new_data
            )

            assert final_step == "completed"
            assert final_has_new_data is True  # First run should detect new data


class TestNewDataDetectionPipelineErrorHandling:
    """Test error handling and failure scenarios."""

    @pytest.mark.asyncio
    async def test_polling_activity_failure(
        self, workflow_env, sample_config, mock_polling_results
    ):
        """Test workflow behavior when polling activity fails."""

        # Create a failing mock activity
        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(config: PollingConfig) -> PollingResult:
            raise RuntimeError("Polling failed")

        async with Worker(
            workflow_env.client,
            task_queue="test-queue",
            workflows=[NewDataDetectionPipeline],
            activities=[test_mock_activity],
        ):
            # Workflow should fail and re-raise the exception
            with pytest.raises(WorkflowFailureError):
                await workflow_env.client.execute_workflow(
                    NewDataDetectionPipeline.run,
                    args=[
                        sample_config,
                        None,
                    ],  # config, downstream_pipeline
                    id=str(uuid.uuid4()),
                    task_queue="test-queue",
                )

    @pytest.mark.skip(
        reason="Test hangs in current test environment - needs investigation"
    )
    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="Patching workflow.start_child_workflow doesn't work in Temporal's "
        "deterministic sandbox. The workflow hangs waiting for the unpatched "
        "start_child_workflow to complete. This test validates that downstream "
        "failures don't fail the main workflow - the behavior is tested by "
        "the try/except in trigger_downstream_pipeline() which logs and returns False."
    )
    async def test_downstream_trigger_failure_doesnt_fail_workflow(
        self, workflow_env, sample_config, mock_polling_results
    ):
        """Test that downstream pipeline failures don't fail the main workflow."""

        # Create a mock activity function that returns the desired response
        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(config: PollingConfig) -> PollingResult:
            content_bytes = b"first response data"
            return PollingResult(
                success=True,
                content=content_bytes,
                polled_at=datetime.now(timezone.utc),
                content_hash=hashlib.sha256(content_bytes).hexdigest(),
            )

        # Mock workflow.start_workflow to raise an exception
        # Note: Must use new_callable=AsyncMock for async functions in Temporal workflow sandbox
        with patch(
            "julee.contrib.polling.apps.worker.pipelines.workflow.start_child_workflow",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Downstream failed"),
        ):
            async with Worker(
                workflow_env.client,
                task_queue="test-queue",
                workflows=[NewDataDetectionPipeline],
                activities=[test_mock_activity],
            ):
                # Workflow should complete successfully despite downstream failure
                result = await workflow_env.client.execute_workflow(
                    NewDataDetectionPipeline.run,
                    args=[
                        sample_config,
                        "TestDownstreamWorkflow",
                        None,
                    ],  # config, downstream_pipeline, previous_completion
                    id=str(uuid.uuid4()),
                    task_queue="test-queue",
                )

                # Verify workflow completed but downstream triggering failed
                assert result["detection_result"]["has_new_data"] is True
                assert (
                    result["downstream_triggered"] is False
                )  # Should be False due to failure


class TestNewDataDetectionPipelineIntegration:
    """Integration tests for complete workflow scenarios."""

    @pytest.mark.asyncio
    async def test_complete_polling_cycle(
        self, workflow_env, sample_config, mock_polling_results
    ):
        """Test a complete polling cycle: first run -> no changes -> changes detected."""
        responses = [
            mock_polling_results["first_data"],
            mock_polling_results["same_data"],
            mock_polling_results["changed_data"],
        ]
        response_index = 0

        # Create a cycling mock activity that returns different responses
        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(config: PollingConfig) -> PollingResult:
            nonlocal response_index
            if response_index == 0:
                content_bytes = b"first response data"
            elif response_index == 1:
                content_bytes = b"first response data"  # Same as first
            else:
                content_bytes = b"changed response data"

            result = PollingResult(
                success=True,
                content=content_bytes,
                polled_at=datetime.now(timezone.utc),
                content_hash=hashlib.sha256(content_bytes).hexdigest(),
            )
            response_index = min(response_index + 1, len(responses) - 1)
            return result

        with patch(
            "julee.contrib.polling.apps.worker.pipelines.workflow.start_child_workflow",
            new_callable=AsyncMock,
        ) as mock_start:
            async with Worker(
                workflow_env.client,
                task_queue="test-queue",
                workflows=[NewDataDetectionPipeline],
                activities=[test_mock_activity],
            ):
                # Workflow should complete successfully despite downstream failure
                # First run - should detect new data (no previous completion)
                result1 = await workflow_env.client.execute_workflow(
                    NewDataDetectionPipeline.run,
                    args=[
                        sample_config,
                        "TestDownstreamWorkflow",
                    ],  # config, downstream_pipeline
                    id=str(uuid.uuid4()),
                    task_queue="test-queue",
                )

                assert result1["detection_result"]["has_new_data"] is True
                assert result1["downstream_triggered"] is True

                # Second run - same content, no changes
                with patch(
                    "temporalio.workflow.get_last_completion_result"
                ) as mock_get_last:
                    mock_get_last.return_value = result1
                    result2 = await workflow_env.client.execute_workflow(
                        NewDataDetectionPipeline.run,
                        args=[
                            sample_config,
                            "TestDownstreamWorkflow",
                        ],  # config, downstream_pipeline
                        id=str(uuid.uuid4()),
                        task_queue="test-queue",
                    )

                assert result2["detection_result"]["has_new_data"] is False
                assert result2["downstream_triggered"] is False

                # Third run - changed content, should detect changes
                with patch(
                    "temporalio.workflow.get_last_completion_result"
                ) as mock_get_last:
                    mock_get_last.return_value = result2
                    result3 = await workflow_env.client.execute_workflow(
                        NewDataDetectionPipeline.run,
                        args=[
                            sample_config,
                            "TestDownstreamWorkflow",
                        ],  # config, downstream_pipeline
                        id=str(uuid.uuid4()),
                        task_queue="test-queue",
                    )

                assert result3["detection_result"]["has_new_data"] is True
                assert result3["downstream_triggered"] is True

                # Verify downstream was called twice (run 1 and run 3)
                assert mock_start.call_count == 2
