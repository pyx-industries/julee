"""What an Acknowledgement promises.

A handler's whole answer. It says whether the handoff was accepted and
carries nothing else, because a handler's answer means one thing and
adding a second would make every handler's answer ambiguous (ADR 003).
"""

import dataclasses

import pytest
from pydantic import BaseModel

from julee.core.entities import kernel_entity_names
from julee.core.entities.acknowledgement import Acknowledgement

pytestmark = pytest.mark.unit


class TestItIsADomainClass:
    """The domain ring holds frozen dataclasses, not pydantic models."""

    def test_it_is_a_dataclass(self) -> None:
        """What the driven port rule requires of anything crossing one.

        Frozen is asserted below, by trying to change one. Reading
        ``__dataclass_params__`` would say the same thing and say it
        worse: ruff wants the attribute and mypy wants the getattr,
        and neither of them is evidence that anything is actually
        immutable.
        """
        assert dataclasses.is_dataclass(Acknowledgement)

    def test_it_is_not_a_pydantic_model(self) -> None:
        """A handler returns this across a driven port, so it may not be."""
        assert not issubclass(Acknowledgement, BaseModel)

    def test_it_cannot_be_changed_after_the_fact(self) -> None:
        """An answer given is an answer given.

        mypy refuses the assignment outright now, which is the better
        half of the guarantee — the ignore below is the evidence. This
        asserts the runtime half, for code mypy never sees.
        """
        with pytest.raises(dataclasses.FrozenInstanceError):
            Acknowledgement.wilco().will_comply = False  # type: ignore[misc]


class TestTheThreeAnswers:
    """Radio procedure: wilco, unable, roger, and nothing else."""

    def test_wilco_will_comply(self) -> None:
        """Received, and will process."""
        assert Acknowledgement.wilco().is_wilco

    def test_unable_will_not(self) -> None:
        """Received, and cannot process."""
        assert Acknowledgement.unable().is_unable

    def test_roger_commits_to_nothing(self) -> None:
        """Received, with no commitment either way."""
        assert Acknowledgement.roger().is_roger

    def test_each_answer_excludes_the_others(self) -> None:
        """Three answers, and exactly one of them at a time."""
        for made in (
            Acknowledgement.wilco(),
            Acknowledgement.unable(),
            Acknowledgement.roger(),
        ):
            assert [made.is_wilco, made.is_unable, made.is_roger].count(True) == 1

    def test_it_carries_what_the_handler_said(self) -> None:
        """The only payload there is, and it is not a result."""
        made = Acknowledgement.unable(info=["schema rejected the payload"])

        assert made.has_info
        assert "schema rejected the payload" in made.info

    def test_two_with_the_same_answer_are_equal(self) -> None:
        """A dataclass compares by value, which a caller may rely on."""
        assert Acknowledgement.wilco(info=["a"]) == Acknowledgement.wilco(info=["a"])


class TestItIsNotARecord:
    """An acknowledgement is not something a repository is bound to.

    Same reasoning as ContentStream: binding is about records. Counting
    it would raise the arity of every handler protocol that returns one,
    which is all of them.
    """

    def test_the_kernel_does_not_offer_it_as_an_entity(self) -> None:
        """Held here so the exclusion is a decision, not a side effect."""
        offered = kernel_entity_names()

        assert "Acknowledgement" not in offered
        assert "Accelerator" in offered, (
            "discovery found nothing, so this proves nothing"
        )
