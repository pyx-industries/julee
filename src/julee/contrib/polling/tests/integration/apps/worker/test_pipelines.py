"""
Integration tests for polling worker pipelines.

This module tests the NewDataDetectionPipeline workflow using Temporal's test
environment. Tests verify the doctrine-compliant pipeline that delegates to
NewDataDetectionUseCase.

These tests require Temporal infrastructure (via WorkflowEnvironment) and are
marked as integration tests.
"""

import hashlib
import uuid
from datetime import datetime, timezone

import pytest
from temporalio import activity
from temporalio.client import WorkflowFailureError
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from julee.contrib.polling.apps.worker.pipelines import NewDataDetectionPipeline
from julee.contrib.polling.entities.polling_config import (
    PollingProtocol,
    PollingResult,
)
from julee.contrib.polling.use_cases import NewDataDetectionRequest

pytestmark = pytest.mark.integration


@pytest.fixture
async def workflow_env():
    """Provide a Temporal test environment with time skipping."""
    async with await WorkflowEnvironment.start_time_skipping(
        data_converter=pydantic_data_converter
    ) as env:
        yield env


@pytest.fixture
def sample_request() -> dict:
    """Provide a sample NewDataDetectionRequest as dict for testing."""
    return NewDataDetectionRequest(
        endpoint_identifier="test-api",
        polling_protocol=PollingProtocol.HTTP,
        connection_params={"url": "https://api.example.com/data"},
        timeout_seconds=30,
    ).model_dump()


class TestNewDataDetectionPipelineFirstRun:
    """Test first run scenarios (no previous completion)."""

    @pytest.mark.asyncio
    async def test_first_run_detects_as_first_poll(self, workflow_env, sample_request):
        """Test first run sets is_first_poll=True."""

        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(request: dict) -> PollingResult:
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
            result = await workflow_env.client.execute_workflow(
                NewDataDetectionPipeline.run,
                args=[sample_request],
                id=str(uuid.uuid4()),
                task_queue="test-queue",
            )

            # Verify first run behavior
            assert result["is_first_poll"] is True
            assert result["success"] is True
            assert result["endpoint_id"] == "test-api"
            assert (
                result["content_hash"]
                == hashlib.sha256(b"first response data").hexdigest()
            )

    @pytest.mark.asyncio
    async def test_first_run_returns_response_structure(
        self, workflow_env, sample_request
    ):
        """Test that response has expected fields from NewDataDetectionResponse."""

        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(request: dict) -> PollingResult:
            content_bytes = b"test content"
            return PollingResult(
                success=True,
                content=content_bytes,
                polled_at=datetime.now(timezone.utc),
            )

        async with Worker(
            workflow_env.client,
            task_queue="test-queue",
            workflows=[NewDataDetectionPipeline],
            activities=[test_mock_activity],
        ):
            result = await workflow_env.client.execute_workflow(
                NewDataDetectionPipeline.run,
                args=[sample_request],
                id=str(uuid.uuid4()),
                task_queue="test-queue",
            )

            # Verify NewDataDetectionResponse structure
            assert "success" in result
            assert "content_hash" in result
            assert "polled_at" in result
            assert "endpoint_id" in result
            assert "has_new_data" in result
            assert "is_first_poll" in result
            assert "dispatches" in result  # From run_next


class TestNewDataDetectionPipelineSubsequentRuns:
    """Test subsequent runs with previous completion data."""

    @pytest.mark.asyncio
    async def test_no_changes_detected(self, workflow_env, sample_request):
        """Test when content hasn't changed since last run."""

        content_bytes = b"same content"
        content_hash = hashlib.sha256(content_bytes).hexdigest()

        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(request: dict) -> PollingResult:
            return PollingResult(
                success=True,
                content=content_bytes,
                polled_at=datetime.now(timezone.utc),
            )

        # Add previous_hash to request (simulating schedule continuation)
        request_with_hash = {**sample_request, "previous_hash": content_hash}

        async with Worker(
            workflow_env.client,
            task_queue="test-queue",
            workflows=[NewDataDetectionPipeline],
            activities=[test_mock_activity],
        ):
            result = await workflow_env.client.execute_workflow(
                NewDataDetectionPipeline.run,
                args=[request_with_hash],
                id=str(uuid.uuid4()),
                task_queue="test-queue",
            )

            # Verify no changes detected
            assert result["has_new_data"] is False
            assert result["is_first_poll"] is False
            assert result["previous_hash"] == content_hash

    @pytest.mark.asyncio
    async def test_changes_detected(self, workflow_env, sample_request):
        """Test when content has changed since last run."""

        old_content_hash = hashlib.sha256(b"old content").hexdigest()
        new_content_bytes = b"new content"

        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(request: dict) -> PollingResult:
            return PollingResult(
                success=True,
                content=new_content_bytes,
                polled_at=datetime.now(timezone.utc),
            )

        request_with_hash = {**sample_request, "previous_hash": old_content_hash}

        async with Worker(
            workflow_env.client,
            task_queue="test-queue",
            workflows=[NewDataDetectionPipeline],
            activities=[test_mock_activity],
        ):
            result = await workflow_env.client.execute_workflow(
                NewDataDetectionPipeline.run,
                args=[request_with_hash],
                id=str(uuid.uuid4()),
                task_queue="test-queue",
            )

            # Verify changes detected
            assert result["has_new_data"] is True
            assert result["is_first_poll"] is False
            assert result["content_hash"] != old_content_hash


class TestNewDataDetectionPipelineWorkflowQueries:
    """Test workflow query methods during execution."""

    @pytest.mark.asyncio
    async def test_workflow_queries(self, workflow_env, sample_request):
        """Test that workflow queries return correct state information."""

        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(request: dict) -> PollingResult:
            await workflow_env.sleep(1)  # Add delay to allow queries
            return PollingResult(
                success=True,
                content=b"test content",
                polled_at=datetime.now(timezone.utc),
            )

        async with Worker(
            workflow_env.client,
            task_queue="test-queue",
            workflows=[NewDataDetectionPipeline],
            activities=[test_mock_activity],
        ):
            handle = await workflow_env.client.start_workflow(
                NewDataDetectionPipeline.run,
                args=[sample_request],
                id=str(uuid.uuid4()),
                task_queue="test-queue",
            )

            # Query state during execution
            endpoint_id = await handle.query(NewDataDetectionPipeline.get_endpoint_id)
            assert endpoint_id == "test-api"

            # Wait for completion
            await handle.result()

            # Query final state
            final_step = await handle.query(NewDataDetectionPipeline.get_current_step)
            assert final_step == "completed"


class TestNewDataDetectionPipelineErrorHandling:
    """Test error handling and failure scenarios."""

    @pytest.mark.asyncio
    async def test_polling_activity_failure(self, workflow_env, sample_request):
        """Test workflow behavior when polling activity fails."""

        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(request: dict) -> PollingResult:
            raise RuntimeError("Polling failed")

        async with Worker(
            workflow_env.client,
            task_queue="test-queue",
            workflows=[NewDataDetectionPipeline],
            activities=[test_mock_activity],
        ):
            with pytest.raises(WorkflowFailureError):
                await workflow_env.client.execute_workflow(
                    NewDataDetectionPipeline.run,
                    args=[sample_request],
                    id=str(uuid.uuid4()),
                    task_queue="test-queue",
                )


class TestNewDataDetectionPipelineRunNext:
    """Test the run_next routing functionality."""

    @pytest.mark.asyncio
    async def test_dispatches_returned_in_response(self, workflow_env, sample_request):
        """Test that dispatches from run_next are included in response."""

        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(request: dict) -> PollingResult:
            return PollingResult(
                success=True,
                content=b"test content",
                polled_at=datetime.now(timezone.utc),
            )

        async with Worker(
            workflow_env.client,
            task_queue="test-queue",
            workflows=[NewDataDetectionPipeline],
            activities=[test_mock_activity],
        ):
            result = await workflow_env.client.execute_workflow(
                NewDataDetectionPipeline.run,
                args=[sample_request],
                id=str(uuid.uuid4()),
                task_queue="test-queue",
            )

            # Dispatches should be present (empty if no routes configured)
            assert "dispatches" in result
            assert isinstance(result["dispatches"], list)


class TestNewDataDetectionPipelineIntegration:
    """Integration tests for complete workflow scenarios."""

    @pytest.mark.asyncio
    async def test_complete_polling_cycle(self, workflow_env, sample_request):
        """Test a complete polling cycle: first run -> no changes -> changes detected."""

        call_count = 0

        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def test_mock_activity(request: dict) -> PollingResult:
            nonlocal call_count
            call_count += 1

            # Return different content on third call
            if call_count <= 2:
                content = b"initial content"
            else:
                content = b"changed content"

            return PollingResult(
                success=True,
                content=content,
                polled_at=datetime.now(timezone.utc),
            )

        async with Worker(
            workflow_env.client,
            task_queue="test-queue",
            workflows=[NewDataDetectionPipeline],
            activities=[test_mock_activity],
        ):
            # First run - is_first_poll=True
            result1 = await workflow_env.client.execute_workflow(
                NewDataDetectionPipeline.run,
                args=[sample_request],
                id=str(uuid.uuid4()),
                task_queue="test-queue",
            )
            assert result1["is_first_poll"] is True

            # Second run - same content, no changes
            request2 = {**sample_request, "previous_hash": result1["content_hash"]}
            result2 = await workflow_env.client.execute_workflow(
                NewDataDetectionPipeline.run,
                args=[request2],
                id=str(uuid.uuid4()),
                task_queue="test-queue",
            )
            assert result2["has_new_data"] is False

            # Third run - changed content
            request3 = {**sample_request, "previous_hash": result2["content_hash"]}
            result3 = await workflow_env.client.execute_workflow(
                NewDataDetectionPipeline.run,
                args=[request3],
                id=str(uuid.uuid4()),
                task_queue="test-queue",
            )
            assert result3["has_new_data"] is True
