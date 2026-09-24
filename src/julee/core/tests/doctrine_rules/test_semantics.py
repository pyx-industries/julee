"""Tests for the semantics rules.

Two of these rules were found passing over data that should have failed
them — once because the rule looked at what a solution adopts rather than
what a kit publishes, and once because it left every far end unchecked.
Both were found by hand: edit a file, run doctrine, watch, put it back.

These are those two afternoons written down, plus the cases nobody has
tried yet. Every rule gets an input that should offend it and one that
should not, because a rule that never fires and a rule that always fires
both look like a passing test suite.

Nothing here touches a filesystem or imports a class. Whether a dotted
path names something is answered by a resolver the test supplies, which
is the whole reason these functions take one.
"""

import pytest

from julee.core.doctrine.rules.semantics import (
    claims_about_classes_not_owned,
    claims_about_missing_classes,
    claims_naming_missing_targets,
    claims_that_contradict,
    claims_that_do_not_resolve,
    claims_without_a_note,
)
from julee.core.entities.claim import Claim, ClaimKind

pytestmark = pytest.mark.unit


def a_claim(
    claim_id: str = "story-projects-usecase",
    source: str = "julee_hcd.domain.models.story.Story",
    kind: ClaimKind = ClaimKind.PROJECTS,
    target: str = "julee.core.entities.use_case.UseCase",
    note: str = "The same event, told from outside.",
) -> Claim:
    """A claim that offends none of the rules, to vary one thing at a time."""
    return Claim(id=claim_id, source=source, kind=kind, target=target, note=note)


def everything_resolves(_dotted_path: str) -> bool:
    """A world where every name is real."""
    return True


def nothing_resolves(_dotted_path: str) -> bool:
    """A world where no name is."""
    return False


def only(*known: str):
    """A world where exactly these names are real."""
    return lambda dotted_path: dotted_path in known


# =============================================================================
# A kit may only claim about what it owns
# =============================================================================


def test_a_claim_about_the_publisher_s_own_class_is_allowed() -> None:
    """The ordinary case, and the one that must not be reported."""
    published = [("julee_hcd", a_claim())]

    assert claims_about_classes_not_owned(published) == []


def test_a_claim_about_another_kit_s_class_is_trespass() -> None:
    """Speaking for people who did not ask."""
    published = [("julee_hcd", a_claim(source="julee_c4.domain.models.Container"))]

    objections = claims_about_classes_not_owned(published)

    assert len(objections) == 1
    assert "does not own" in objections[0]


def test_the_objection_names_the_claim_and_the_class() -> None:
    """Whoever has to fix it needs to know which claim and which class."""
    published = [
        ("julee_hcd", a_claim(claim_id="wrong", source="julee_c4.models.Container"))
    ]

    objection = claims_about_classes_not_owned(published)[0]

    assert "wrong" in objection
    assert "julee_c4.models.Container" in objection
    assert "julee_hcd" in objection


def test_a_package_whose_name_prefixes_another_is_not_confused() -> None:
    """julee_hcd does not own julee_hcd_extras.Thing."""
    published = [("julee_hcd", a_claim(source="julee_hcd_extras.models.Thing"))]

    assert claims_about_classes_not_owned(published) != []


# =============================================================================
# A claim should say why
# =============================================================================


def test_a_claim_with_a_note_is_allowed() -> None:
    """The note is what makes this documentation."""
    assert claims_without_a_note([("julee_hcd", a_claim())]) == []


@pytest.mark.parametrize("note", ["", "   ", "\n\n"])
def test_a_claim_with_nothing_to_say_is_reported(note: str) -> None:
    """Whitespace is not an explanation."""
    assert claims_without_a_note([("julee_hcd", a_claim(note=note))]) != []


# =============================================================================
# The near end must name something
# =============================================================================


def test_a_claim_about_a_real_class_is_allowed() -> None:
    """The ordinary case."""
    published = [("julee_hcd", a_claim())]

    assert claims_about_missing_classes(published, everything_resolves) == []


def test_a_claim_about_a_renamed_class_is_reported() -> None:
    """The regression from #204: misspelling this used to pass."""
    published = [("julee_hcd", a_claim(source="julee_hcd.models.Storey"))]

    assert claims_about_missing_classes(published, nothing_resolves) != []


def test_the_far_end_is_not_checked_by_this_rule() -> None:
    """A kit checks its near ends; the far end has its own rule and reasons."""
    published = [("julee_hcd", a_claim())]
    resolves = only("julee_hcd.domain.models.story.Story")

    assert claims_about_missing_classes(published, resolves) == []


# =============================================================================
# The far end, when it can be checked
# =============================================================================


def test_a_far_end_in_a_package_nobody_installed_is_left_alone() -> None:
    """Which is how a claim stays useful to a solution that adopts both."""
    published = [("julee_hcd", a_claim(target="julee_c4.models.Container"))]

    objections = claims_naming_missing_targets(
        published, nothing_resolves, package_present=nothing_resolves
    )

    assert objections == []


def test_a_far_end_in_an_installed_package_must_be_right() -> None:
    """The regression from #205: the kernel is always installed."""
    published = [
        ("julee_hcd", a_claim(target="julee.core.entities.accelerator.Accelarator"))
    ]

    objections = claims_naming_missing_targets(
        published, nothing_resolves, package_present=everything_resolves
    )

    assert len(objections) == 1
    assert "Accelarator" in objections[0]


def test_a_far_end_that_is_present_and_right_is_allowed() -> None:
    """The case that must stay quiet, or the rule is useless."""
    published = [("julee_hcd", a_claim())]

    objections = claims_naming_missing_targets(
        published, everything_resolves, package_present=everything_resolves
    )

    assert objections == []


# =============================================================================
# What a solution holds true is checked at both ends
# =============================================================================


def test_an_accepted_claim_with_both_ends_real_is_allowed() -> None:
    """The ordinary case."""
    assert claims_that_do_not_resolve([a_claim()], everything_resolves) == []


def test_an_accepted_claim_is_checked_at_both_ends() -> None:
    """Unlike a published one: by now every kit named has been adopted."""
    resolves = only("julee_hcd.domain.models.story.Story")

    objections = claims_that_do_not_resolve([a_claim()], resolves)

    assert len(objections) == 1
    assert "julee.core.entities.use_case.UseCase" in objections[0]


def test_both_ends_being_wrong_is_reported_twice() -> None:
    """Two things to fix, so two objections."""
    assert len(claims_that_do_not_resolve([a_claim()], nothing_resolves)) == 2


# =============================================================================
# One pair, one answer
# =============================================================================


def test_two_claims_about_different_pairs_do_not_contradict() -> None:
    """Most claims are about different things."""
    claims = [a_claim(claim_id="one"), a_claim(claim_id="two", target="other.Thing")]

    assert claims_that_contradict(claims) == []


def test_the_same_pair_claimed_the_same_way_twice_is_not_a_contradiction() -> None:
    """Two kits agreeing is not a disagreement."""
    claims = [a_claim(claim_id="one"), a_claim(claim_id="two")]

    assert claims_that_contradict(claims) == []


def test_the_same_pair_claimed_two_ways_is_a_contradiction() -> None:
    """Which the solution must settle, rather than holding both."""
    claims = [a_claim(claim_id="one"), a_claim(claim_id="two", kind=ClaimKind.IS_A)]

    objections = claims_that_contradict(claims)

    assert len(objections) == 1
    assert "one" in objections[0]
    assert "two" in objections[0]


def test_a_contradiction_names_both_kinds_so_the_reader_can_choose() -> None:
    """The point of the message is to let someone decline the wrong one."""
    claims = [a_claim(claim_id="one"), a_claim(claim_id="two", kind=ClaimKind.IS_A)]

    objection = claims_that_contradict(claims)[0]

    assert "projects" in objection
    assert "is_a" in objection


def test_direction_matters_so_a_reversed_pair_is_a_different_claim() -> None:
    """A contains B and B contains A are not the same statement."""
    claims = [
        a_claim(claim_id="one", source="a.A", target="b.B"),
        a_claim(claim_id="two", source="b.B", target="a.A"),
    ]

    assert claims_that_contradict(claims) == []


# =============================================================================
# Nothing at all
# =============================================================================


@pytest.mark.parametrize(
    "rule",
    [
        lambda: claims_about_classes_not_owned([]),
        lambda: claims_without_a_note([]),
        lambda: claims_about_missing_classes([], nothing_resolves),
        lambda: claims_naming_missing_targets([], nothing_resolves, nothing_resolves),
        lambda: claims_that_do_not_resolve([], nothing_resolves),
        lambda: claims_that_contradict([]),
    ],
)
def test_a_codebase_claiming_nothing_offends_nothing(rule) -> None:
    """Which is every codebase today, and must stay quiet rather than fail."""
    assert rule() == []
