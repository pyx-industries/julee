"""
Integration tests for polling worker pipelines.

These run NewDataDetectionPipeline through Temporal's time-skipping test
environment: the poll_endpoint activity is a stand-in, and the workflow
orchestration around it is real.

NewDataDetectionPipeline is abstract - a solution subclasses it to supply
a handler and an analyzer - so the tests run a subclass of their own,
whose handler records what it is given.

Every workflow is started with an execution timeout. A workflow that
raises anything other than a Temporal failure does not fail: Temporal
retries the workflow task for ever, and a test awaiting its result never
returns. With the timeout, that mistake is a failing test.
"""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

import pytest
from temporalio import activity, workflow
from temporalio.client import WorkflowFailureError, WorkflowHandle
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from julee.contrib.polling.apps.worker.pipelines import NewDataDetectionPipeline
from julee.contrib.polling.domain.models.polling_config import (
    PollingConfig,
    PollingProtocol,
    PollingResult,
)
from julee.core.entities.acknowledgement import Acknowledgement

# Each test starts a Temporal test server, so these are not unit tests.
pytestmark = pytest.mark.integration

TASK_QUEUE = "test-queue"
EXECUTION_TIMEOUT = timedelta(seconds=30)

FIRST_CONTENT = b"first response data"
CHANGED_CONTENT = b"changed response data"


def content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class RecordingHandler:
    """A PollingResultHandler that remembers what it was handed."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def handle_new_data(
        self,
        endpoint_id: str,
        new_item_ids: list[str],
        content_hash: str,
    ) -> Acknowledgement:
        self.calls.append(
            {
                "endpoint_id": endpoint_id,
                "new_item_ids": new_item_ids,
                "content_hash": content_hash,
            }
        )
        return Acknowledgement.wilco()


class FailingHandler:
    """A PollingResultHandler that cannot cope."""

    async def handle_new_data(
        self,
        endpoint_id: str,
        new_item_ids: list[str],
        content_hash: str,
    ) -> Acknowledgement:
        raise RuntimeError("Handler failed")


class WholePayloadAnalyzer:
    """A NewDataAnalyzer that treats each payload as a single item."""

    async def identify_new_items(
        self,
        previous_data: bytes | None,
        new_data: bytes,
    ) -> list[str]:
        return [new_data.decode()]


@workflow.defn
class RecordingPipeline(NewDataDetectionPipeline):
    """The pipeline as a solution would subclass it, with a query to see
    what reached the handler."""

    def __init__(self) -> None:
        super().__init__()
        self._handler = RecordingHandler()

    def get_handler(self) -> RecordingHandler:
        return self._handler

    def get_analyzer(self) -> WholePayloadAnalyzer:
        return WholePayloadAnalyzer()

    @workflow.run
    async def run(self, config: PollingConfig | dict[str, Any]) -> dict[str, Any]:
        return await super().run(config)

    @workflow.query
    def get_handled(self) -> list[dict[str, Any]]:
        return self._handler.calls


@workflow.defn
class FailingHandlerPipeline(NewDataDetectionPipeline):
    """The pipeline with a handler that raises."""

    def get_handler(self) -> FailingHandler:
        return FailingHandler()

    def get_analyzer(self) -> WholePayloadAnalyzer:
        return WholePayloadAnalyzer()

    @workflow.run
    async def run(self, config: PollingConfig | dict[str, Any]) -> dict[str, Any]:
        return await super().run(config)


def poll_endpoint_returning(*contents: bytes) -> Any:
    """A poll_endpoint activity that returns each content in turn, then
    goes on returning the last."""
    remaining = list(contents)

    @activity.defn(name="julee.contrib.polling.poll_endpoint")
    async def poll_endpoint(config: PollingConfig) -> PollingResult:
        content = remaining.pop(0) if len(remaining) > 1 else remaining[0]
        return PollingResult(
            success=True,
            content=content,
            polled_at=datetime.now(UTC),
            content_hash=content_hash(content),
        )

    return poll_endpoint


def completion_for(content: bytes) -> dict[str, Any]:
    """What an earlier run that polled this content would have returned."""
    return {
        "polling_result": {
            "content_hash": content_hash(content),
            "content": content.decode(),
            "polled_at": "2023-01-01T00:00:00+00:00",
        },
        "detection_result": {
            "has_new_data": True,
            "current_hash": content_hash(content),
        },
        "endpoint_id": "test-api",
        "completed_at": "2023-01-01T00:00:00+00:00",
    }


def last_completion(completion: dict[str, Any] | None) -> Any:
    """Have the workflow see this as the schedule's last completion result."""
    return patch(
        "temporalio.workflow.get_last_completion_result",
        return_value=completion,
    )


async def start_pipeline(
    env: WorkflowEnvironment,
    config: PollingConfig,
    pipeline: type[NewDataDetectionPipeline] = RecordingPipeline,
) -> WorkflowHandle[Any, dict[str, Any]]:
    return await env.client.start_workflow(
        pipeline.run,
        config,
        id=str(uuid.uuid4()),
        task_queue=TASK_QUEUE,
        execution_timeout=EXECUTION_TIMEOUT,
    )


async def run_pipeline(
    env: WorkflowEnvironment,
    config: PollingConfig,
    previous_completion: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run RecordingPipeline as the run after previous_completion, and
    return its result with what reached the handler.

    The handler is asked about while the last completion result is still
    patched. A query on a finished workflow replays it, and a replay that
    saw a different last completion would take a different path.
    """
    with last_completion(previous_completion):
        handle = await start_pipeline(env, config)
        result = await handle.result()
        handled = await handle.query(RecordingPipeline.get_handled)
    return result, handled


# Each test starts a Temporal test server, so these are integration tests
# however fast they look. Run them with -m integration.
pytestmark = pytest.mark.integration


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


def worker(env: WorkflowEnvironment, poll_endpoint: Any) -> Worker:
    return Worker(
        env.client,
        task_queue=TASK_QUEUE,
        workflows=[RecordingPipeline, FailingHandlerPipeline],
        activities=[poll_endpoint],
    )


class TestNewDataDetectionPipelineFirstRun:
    """Test first run scenarios (no previous completion)."""

    async def test_first_run_detects_new_data(self, workflow_env, sample_config):
        """With nothing to compare against, whatever is polled is new."""
        async with worker(workflow_env, poll_endpoint_returning(FIRST_CONTENT)):
            result, _ = await run_pipeline(workflow_env, sample_config)

        assert result["detection_result"]["has_new_data"] is True
        assert result["detection_result"]["current_hash"] == content_hash(FIRST_CONTENT)
        assert result["endpoint_id"] == "test-api"

    async def test_completion_carries_what_the_next_run_compares(
        self, workflow_env, sample_config
    ):
        """The result is the next run's last completion result, so it holds
        the content and its hash."""
        async with worker(workflow_env, poll_endpoint_returning(FIRST_CONTENT)):
            result, _ = await run_pipeline(workflow_env, sample_config)

        polling_result = result["polling_result"]
        assert polling_result["content_hash"] == content_hash(FIRST_CONTENT)
        assert polling_result["content"] == FIRST_CONTENT.decode()
        assert "polled_at" in polling_result
        assert "completed_at" in result

    async def test_first_run_hands_new_items_to_handler(
        self, workflow_env, sample_config
    ):
        """The handler gets the analyzer's item IDs, not the raw bytes."""
        async with worker(workflow_env, poll_endpoint_returning(FIRST_CONTENT)):
            _, handled = await run_pipeline(workflow_env, sample_config)

        assert handled == [
            {
                "endpoint_id": "test-api",
                "new_item_ids": [FIRST_CONTENT.decode()],
                "content_hash": content_hash(FIRST_CONTENT),
            }
        ]

    async def test_config_may_arrive_as_dict(self, workflow_env, sample_config):
        """A Temporal schedule serialises its args, so config comes as a dict."""
        async with worker(workflow_env, poll_endpoint_returning(FIRST_CONTENT)):
            with last_completion(None):
                result = await workflow_env.client.execute_workflow(
                    RecordingPipeline.run,
                    sample_config.model_dump(mode="json"),
                    id=str(uuid.uuid4()),
                    task_queue=TASK_QUEUE,
                    execution_timeout=EXECUTION_TIMEOUT,
                )

        assert result["endpoint_id"] == "test-api"


class TestNewDataDetectionPipelineSubsequentRuns:
    """Test subsequent runs with previous completion data."""

    async def test_no_changes_detected(self, workflow_env, sample_config):
        """The same content as last time is not new, and the handler is
        left alone."""
        async with worker(workflow_env, poll_endpoint_returning(FIRST_CONTENT)):
            result, handled = await run_pipeline(
                workflow_env, sample_config, completion_for(FIRST_CONTENT)
            )

        assert result["detection_result"]["has_new_data"] is False
        assert handled == []

    async def test_changes_detected(self, workflow_env, sample_config):
        """Different content from last time is new, and goes to the handler."""
        async with worker(workflow_env, poll_endpoint_returning(CHANGED_CONTENT)):
            result, handled = await run_pipeline(
                workflow_env, sample_config, completion_for(FIRST_CONTENT)
            )

        assert result["detection_result"]["has_new_data"] is True
        assert result["detection_result"]["current_hash"] == content_hash(
            CHANGED_CONTENT
        )
        assert [call["new_item_ids"] for call in handled] == [
            [CHANGED_CONTENT.decode()]
        ]


class TestNewDataDetectionPipelineWorkflowQueries:
    """Test workflow query methods."""

    async def test_workflow_queries(self, workflow_env, sample_config):
        """The queries report where the workflow got to and what it found."""
        async with worker(workflow_env, poll_endpoint_returning(FIRST_CONTENT)):
            with last_completion(None):
                handle = await start_pipeline(workflow_env, sample_config)
                await handle.result()

                step = await handle.query(NewDataDetectionPipeline.get_current_step)
                endpoint_id = await handle.query(
                    NewDataDetectionPipeline.get_endpoint_id
                )
                has_new_data = await handle.query(
                    NewDataDetectionPipeline.get_has_new_data
                )

        assert step == "completed"
        assert endpoint_id == "test-api"
        assert has_new_data is True


class TestNewDataDetectionPipelineErrorHandling:
    """Test error handling and failure scenarios."""

    async def test_polling_activity_failure(self, workflow_env, sample_config):
        """When polling keeps failing, the workflow fails."""

        @activity.defn(name="julee.contrib.polling.poll_endpoint")
        async def failing_poll_endpoint(config: PollingConfig) -> PollingResult:
            raise RuntimeError("Polling failed")

        async with worker(workflow_env, failing_poll_endpoint):
            with last_completion(None):
                handle = await start_pipeline(workflow_env, sample_config)
                with pytest.raises(WorkflowFailureError):
                    await handle.result()

    async def test_handler_failure_does_not_fail_workflow(
        self, workflow_env, sample_config
    ):
        """A handler that raises does not lose the poll: the run completes,
        so the next one still has something to compare against."""
        async with worker(workflow_env, poll_endpoint_returning(FIRST_CONTENT)):
            with last_completion(None):
                handle = await start_pipeline(
                    workflow_env, sample_config, FailingHandlerPipeline
                )
                result = await handle.result()

        assert result["detection_result"]["has_new_data"] is True
        assert result["polling_result"]["content_hash"] == content_hash(FIRST_CONTENT)


class TestNewDataDetectionPipelineIntegration:
    """Test a sequence of runs, each fed the one before."""

    async def test_complete_polling_cycle(self, workflow_env, sample_config):
        """First run, then no change, then a change."""
        poll_endpoint = poll_endpoint_returning(
            FIRST_CONTENT, FIRST_CONTENT, CHANGED_CONTENT
        )

        async with worker(workflow_env, poll_endpoint):
            first, _ = await run_pipeline(workflow_env, sample_config)
            second, _ = await run_pipeline(workflow_env, sample_config, first)
            third, _ = await run_pipeline(workflow_env, sample_config, second)

        assert first["detection_result"]["has_new_data"] is True
        assert second["detection_result"]["has_new_data"] is False
        assert third["detection_result"]["has_new_data"] is True
