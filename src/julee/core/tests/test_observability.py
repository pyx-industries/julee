"""What an adapter can find out about the execution it is serving.

The thread through a log. A use case does not log (ADR 017), so if this
is wrong the symptom is not a crash — it is a production log where twelve
adapter events from one run cannot be told from twelve unrelated ones.
That is worth testing directly rather than trusting.
"""

import asyncio
import logging

import pytest

from julee.core.observability import (
    ExecutionIdFilter,
    execution_id,
    log_extra,
    serving,
)
from julee.core.witnesses.execution import DefaultExecutionWitness

pytestmark = pytest.mark.unit


class TestWhoIsBeingServed:
    """What execution_id answers, inside a run and outside one."""

    def test_outside_any_execution_it_is_empty(self) -> None:
        """An adapter called by nobody in particular still works.

        A missing thread is a worse log, not a broken run, so this
        answers "" rather than raising.
        """
        assert execution_id() == ""

    def test_inside_one_it_is_that_execution(self) -> None:
        """What the witness said."""
        witness = DefaultExecutionWitness("run-1")

        with serving(witness):
            assert execution_id() == "run-1"

    def test_it_yields_the_identifier_too(self) -> None:
        """So a caller that wants to log the start of a run has it."""
        with serving(DefaultExecutionWitness("run-1")) as identifier:
            assert identifier == "run-1"

    def test_afterwards_it_is_empty_again(self) -> None:
        """A run that has ended is not still being served.

        Without the reset, a pooled worker thread would attribute the
        next run's events to this one — which is worse than no thread,
        because it reads as true.
        """
        with serving(DefaultExecutionWitness("run-1")):
            pass

        assert execution_id() == ""

    def test_it_is_restored_even_if_the_run_raises(self) -> None:
        """A failed run must not leak its identifier into the next."""
        with pytest.raises(RuntimeError), serving(DefaultExecutionWitness("run-1")):
            raise RuntimeError("the run failed")

        assert execution_id() == ""

    def test_a_nested_run_is_restored_to_the_outer_one(self) -> None:
        """Nesting is not expected, but it must not corrupt the outer."""
        with serving(DefaultExecutionWitness("outer")):
            with serving(DefaultExecutionWitness("inner")):
                assert execution_id() == "inner"

            assert execution_id() == "outer"

    def test_the_witness_is_asked_once(self) -> None:
        """Not once per adapter.

        A witness that minted a fresh identifier per call would give
        every adapter a different thread, which is the failure this
        whole mechanism exists to prevent — and DefaultExecutionWitness
        with no argument does mint one per instance.
        """
        witness = DefaultExecutionWitness()

        with serving(witness) as first:
            seen = [execution_id(), execution_id()]

        assert seen == [first, first]


class TestConcurrentRuns:
    """Two runs at once must not read each other's identifier."""

    async def test_each_task_sees_its_own(self) -> None:
        """The reason this is a ContextVar and not a module global.

        A module-level variable would pass every test above and fail
        here, which is exactly the shape of bug that reaches production
        in an async worker.
        """

        async def run(name: str) -> str:
            with serving(DefaultExecutionWitness(name)):
                await asyncio.sleep(0)
                return execution_id()

        # list(), because gather returns one at runtime and the typed
        # overload says tuple. Comparing to either alone satisfies one
        # and fails the other.
        assert list(await asyncio.gather(run("a"), run("b"))) == ["a", "b"]


class TestWhatAnAdapterLogs:
    """log_extra carries the thread without the adapter remembering to."""

    def test_it_adds_the_identifier(self) -> None:
        """Alongside whatever the event was about."""
        with serving(DefaultExecutionWitness("run-1")):
            assert log_extra(size=3) == {"size": 3, "execution_id": "run-1"}

    def test_it_leaves_the_fields_alone(self) -> None:
        """An adapter's own fields are not renamed or dropped."""
        with serving(DefaultExecutionWitness("run-1")):
            found = log_extra(document_id="d-1", size=3)

        assert found["document_id"] == "d-1"
        assert found["size"] == 3

    def test_outside_an_execution_it_adds_nothing(self) -> None:
        """Rather than an empty execution_id, which reads as a real one."""
        assert log_extra(size=3) == {"size": 3}


class TestTheLoggingFilter:
    """For a solution that formats rather than reads extra."""

    def a_record(self) -> logging.LogRecord:
        """One record, as a handler would see it."""
        return logging.LogRecord(
            name="adapter",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="stored",
            args=(),
            exc_info=None,
        )

    def test_it_puts_the_identifier_on_the_record(self) -> None:
        """So %(execution_id)s works in a format string."""
        record = self.a_record()

        with serving(DefaultExecutionWitness("run-1")):
            ExecutionIdFilter().filter(record)

        assert record.execution_id == "run-1"  # type: ignore[attr-defined]

    def test_a_record_from_outside_still_formats(self) -> None:
        """Empty rather than absent: a missing attribute raises in the
        formatter, and a broken formatter loses the whole log."""
        record = self.a_record()

        ExecutionIdFilter().filter(record)

        assert record.execution_id == ""  # type: ignore[attr-defined]

    def test_it_keeps_the_record(self) -> None:
        """This filter adds rather than excludes, so nothing is dropped."""
        assert ExecutionIdFilter().filter(self.a_record()) is True
