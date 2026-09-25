"""Tests for the witnesses, and for the names they used to have.

ADR 016 renamed ClockService and ExecutionService to ClockWitness and
ExecutionWitness. Neither was ever a service under ADR 009's rule, which
binds a service to two or more entity types; both are bound to none.

Every solution built on julee injects these two, so the old names keep
working for a release rather than being cut. These tests are what makes
that promise checkable, and what will fail loudly when the shim is
finally removed on purpose.
"""

import warnings

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


# =============================================================================
# The names they used to have
# =============================================================================


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("ClockService", ClockWitness),
        ("SystemClockService", SystemClockWitness),
        ("ExecutionService", ExecutionWitness),
        ("DefaultExecutionService", DefaultExecutionWitness),
    ],
)
def test_an_old_name_still_resolves_to_the_new_object(old: str, new: type) -> None:
    """Not a copy: the same object, so isinstance and typing still hold."""
    import julee.core.services as shim

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        assert getattr(shim, old) is new


def test_the_old_submodule_path_still_imports() -> None:
    """ceap imports julee.core.services.execution directly.

    A package-level __getattr__ would not cover that, so the submodules
    are shimmed too. This test is the reason both exist.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from julee.core.services.execution import DefaultExecutionService

    assert DefaultExecutionService is DefaultExecutionWitness


def test_using_an_old_name_warns() -> None:
    """A silent alias would leave nobody any reason to move."""
    import julee.core.services as shim

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert shim.ClockService is ClockWitness

    assert len(caught) == 1
    assert issubclass(caught[0].category, DeprecationWarning)


def test_the_warning_says_what_to_import_instead() -> None:
    """An author reading it should not have to go looking."""
    import julee.core.services as shim

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert shim.ExecutionService is ExecutionWitness

    message = str(caught[0].message)
    assert "julee.core.witnesses.ExecutionWitness" in message
    assert "ADR 016" in message


def test_a_name_that_was_never_there_still_raises() -> None:
    """The shim answers for four names, not for anything asked of it."""
    import julee.core.services as shim

    with pytest.raises(AttributeError):
        _ = shim.NoSuchService
