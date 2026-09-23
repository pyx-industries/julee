"""Tests for the use case step decorator.

The decorator exists so a use case reads as its business logic: each step
logs either side of itself, and a failing step says which step it was
before the exception carries on.
"""

import logging

import pytest

from julee.core.usecases.decorators import try_use_case_step

pytestmark = pytest.mark.unit


async def test_the_result_is_returned_unchanged() -> None:
    @try_use_case_step("generate_id")
    async def step() -> str:
        return "doc-123"

    assert await step() == "doc-123"


async def test_arguments_reach_the_step() -> None:
    @try_use_case_step("save")
    async def step(a: int, *, b: int) -> int:
        return a + b

    assert await step(1, b=2) == 3


async def test_a_failing_step_raises_what_it_raised() -> None:
    @try_use_case_step("fetch_schema")
    async def step() -> None:
        raise ValueError("no such schema")

    with pytest.raises(ValueError, match="no such schema"):
        await step()


async def test_a_failing_step_is_logged_with_its_name(caplog) -> None:
    """The point of the decorator: the log says which step failed."""

    @try_use_case_step("fetch_schema")
    async def step() -> None:
        raise ValueError("no such schema")

    with caplog.at_level(logging.ERROR), pytest.raises(ValueError):
        await step()

    (record,) = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert "fetch_schema" in record.getMessage()
    assert record.error_type == "ValueError"
    assert record.debug_step == "fetch_schema_failed"


async def test_extra_context_reaches_every_record(caplog) -> None:
    @try_use_case_step("assemble", {"document_id": "doc-123"})
    async def step() -> None:
        raise RuntimeError("boom")

    with caplog.at_level(logging.DEBUG), pytest.raises(RuntimeError):
        await step()

    assert [r.document_id for r in caplog.records] == ["doc-123", "doc-123"]


async def test_a_successful_step_logs_before_and_after(caplog) -> None:
    @try_use_case_step("generate_id")
    async def step() -> str:
        return "doc-123"

    with caplog.at_level(logging.DEBUG):
        await step()

    assert [r.debug_step for r in caplog.records] == [
        "before_generate_id",
        "generate_id_success",
    ]


async def test_a_string_result_is_logged_as_the_result(caplog) -> None:
    @try_use_case_step("generate_id")
    async def step() -> str:
        return "doc-123"

    with caplog.at_level(logging.DEBUG):
        await step()

    success = caplog.records[-1]
    assert success.result == "doc-123"


async def test_an_object_result_is_logged_by_type_not_by_value(caplog) -> None:
    """A step may return an entity; the log names it rather than dumping it."""

    class Assembly:
        pass

    @try_use_case_step("assemble")
    async def step() -> Assembly:
        return Assembly()

    with caplog.at_level(logging.DEBUG):
        await step()

    success = caplog.records[-1]
    assert success.result_type == "Assembly"
    assert not hasattr(success, "result")


async def test_the_step_keeps_its_name_and_docstring() -> None:
    @try_use_case_step("generate_id")
    async def generate_id() -> str:
        """Generate an id."""
        return "doc-123"

    assert generate_id.__name__ == "generate_id"
    assert generate_id.__doc__ == "Generate an id."
