"""What a workflow proxy hands back when the port promises a container.

A proxy calls an activity and tells the data converter what to decode
the result into. For ``get(id) -> Story | None`` it hands over
``Story`` and a Story comes back. For ``get_many(ids) -> dict[str, Story
| None]`` and ``list_all() -> list[Story]`` it handed over nothing —
``_is_decodable_type`` refused anything that was not a bare class — and
the converter, given no type, answered with dicts.

ceap's assembling use case has carried a thirty-line comment and a loop
of single ``get()`` calls to work around that since it was written, and
the comment blamed Temporal's type resolution. It is this decorator's.

Through a real ``WorkflowEnvironment``: the activity runs, the payload
crosses, the converter decodes, and the workflow reports the Python
types it was handed. Nothing here is mocked, because a mock of the
converter would answer whatever the test told it to.
"""

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

import pytest
from temporalio import workflow
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from julee.core.repositories.base import BaseRepository
from julee.integrations.temporal.activities import collect_activities_from_instances
from julee.integrations.temporal.decorators import (
    temporal_activity_registration,
    temporal_workflow_proxy,
)

pytestmark = pytest.mark.integration

ACTIVITY_BASE = "test.stories"
TASK_QUEUE = "generic-returns"


@dataclass(frozen=True)
class Story:
    """An entity, as the estate writes one."""

    slug: str
    title: str = ""


class StoryRepository(BaseRepository[Story], Protocol):
    """The port, with get_many and list_all from the kernel base."""


class MemoryStories:
    """The adapter behind the activities."""

    def __init__(self) -> None:
        self.kept: dict[str, Story] = {}

    async def get(self, entity_id: str) -> Story | None:
        return self.kept.get(entity_id)

    async def get_many(self, entity_ids: list[str]) -> dict[str, Story | None]:
        return {entity_id: self.kept.get(entity_id) for entity_id in entity_ids}

    async def list_all(self) -> list[Story]:
        return list(self.kept.values())

    async def save(self, entity: Story) -> None:
        self.kept[entity.slug] = entity

    async def generate_id(self) -> str:
        return f"story-{uuid.uuid4()}"


@temporal_activity_registration(ACTIVITY_BASE)
class TemporalMemoryStories(MemoryStories, StoryRepository):
    """The activity twin, as a kit declares one."""


@temporal_workflow_proxy(ACTIVITY_BASE)
class WorkflowStoriesProxy(StoryRepository):
    """The workflow-side twin, as a kit declares one."""


@dataclass(frozen=True)
class WhatCameBack:
    """The Python type names the workflow was handed, per method."""

    from_get: str
    from_get_many: list[str]
    from_list_all: list[str]
    missing_is_none: bool


@workflow.defn
class AskForStories:
    """Calls each read through the proxy and reports what it received."""

    @workflow.run
    async def run(self, slugs: list[str]) -> WhatCameBack:
        stories: StoryRepository = WorkflowStoriesProxy()  # type: ignore[abstract]
        one = await stories.get(slugs[0])
        many = await stories.get_many([*slugs, "nobody"])
        every = await stories.list_all()
        return WhatCameBack(
            from_get=type(one).__name__,
            from_get_many=[type(many[slug]).__name__ for slug in slugs],
            from_list_all=[type(story).__name__ for story in every],
            missing_is_none=many["nobody"] is None,
        )


@pytest.fixture
async def env() -> AsyncIterator[WorkflowEnvironment]:
    """A time-skipping Temporal, with the converter the kits' workers use."""
    async with await WorkflowEnvironment.start_time_skipping(
        data_converter=pydantic_data_converter
    ) as started:
        yield started


async def what_the_workflow_got(client: Client, stories: MemoryStories) -> WhatCameBack:
    """Run the workflow against a worker serving the given adapter.

    Args:
        client: The environment's client
        stories: The adapter whose stories the activities read

    Returns:
        What the workflow reported
    """
    async with Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[AskForStories],
        activities=collect_activities_from_instances(stories),
    ):
        return await client.execute_workflow(
            AskForStories.run,
            ["a", "b"],
            id=f"ask-{uuid.uuid4()}",
            task_queue=TASK_QUEUE,
        )


async def test_a_single_entity_comes_back_as_itself(env: WorkflowEnvironment) -> None:
    """The case that already worked: a bare class as result_type."""
    stories = TemporalMemoryStories()
    await stories.save(Story(slug="a", title="A"))
    await stories.save(Story(slug="b", title="B"))

    got = await what_the_workflow_got(env.client, stories)

    assert got.from_get == "Story"


async def test_get_many_hands_back_entities_not_dicts(env: WorkflowEnvironment) -> None:
    """The defect ceap worked around in its use case.

    dict[str, Story | None] is what the port promises. The proxy has to
    hand that to the converter as it is, and the converter builds it.
    """
    stories = TemporalMemoryStories()
    await stories.save(Story(slug="a", title="A"))
    await stories.save(Story(slug="b", title="B"))

    got = await what_the_workflow_got(env.client, stories)

    assert got.from_get_many == ["Story", "Story"]
    assert got.missing_is_none


async def test_list_all_hands_back_entities_not_dicts(env: WorkflowEnvironment) -> None:
    """Every List use case behind a proxy went through this and got dicts."""
    stories = TemporalMemoryStories()
    await stories.save(Story(slug="a", title="A"))
    await stories.save(Story(slug="b", title="B"))

    got = await what_the_workflow_got(env.client, stories)

    assert got.from_list_all == ["Story", "Story"]
