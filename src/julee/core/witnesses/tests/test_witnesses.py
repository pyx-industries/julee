"""Tests for the two witnesses.

ADR 016 renamed ClockService and ExecutionService to ClockWitness and
ExecutionWitness. Neither was ever a service under ADR 009's rule, which
binds a service to two or more entity types; both are bound to none.

The old names were kept working for one release, which was 0.7.0, and
are gone. Nothing in julee or in any kit imported them by then.
"""

import importlib

import pytest

from julee.core.witnesses import (
    ClockWitness,
    DefaultExecutionWitness,
    ExecutionWitness,
    SystemClockWitness,
)

pytestmark = pytest.mark.unit


def test_a_system_clock_reports_an_aware_time() -> None:
    assert SystemClockWitness().now().tzinfo is not None


def test_an_execution_witness_keeps_one_identity() -> None:
    """The identifier is per execution, not per call."""
    witness = DefaultExecutionWitness()

    assert witness.get_execution_id() == witness.get_execution_id()


def test_an_execution_witness_can_be_told_what_to_say() -> None:
    """Tests need a fixed identity; the default mints one."""
    assert DefaultExecutionWitness("run-1").get_execution_id() == "run-1"


def test_two_default_witnesses_do_not_share_an_identity() -> None:
    assert (
        DefaultExecutionWitness().get_execution_id()
        != DefaultExecutionWitness().get_execution_id()
    )


def test_the_implementations_satisfy_their_protocols() -> None:
    """Structural, so this is what binds the two halves together."""
    clock: ClockWitness = SystemClockWitness()
    execution: ExecutionWitness = DefaultExecutionWitness()

    assert clock.now() is not None
    assert execution.get_execution_id()


def test_the_old_module_is_gone() -> None:
    """The shim was for one release, and this is what ends it.

    Kept as a test rather than deleted with the code, because an
    accidental resurrection — a stray file, a bad merge — would otherwise
    be silent, and the whole point of the removal was to stop two names
    meaning one thing.
    """
    with pytest.raises(ImportError):
        # Through importlib rather than an import statement: mypy
        # objects to the latter naming a module that is not there,
        # which is exactly what this asserts.
        importlib.import_module("julee.core.services")
