"""Tests for joining declarations to the parser's families."""

import pytest

from julee.core.census import FAMILY_DIRECTORIES, census_of_context, families_of
from julee.core.entities.bounded_context_info import BoundedContextInfo
from julee.core.parsers.declarations import BINDING, CLASS, FUNCTION
from julee.core.values.census import (
    AMBIGUOUS,
    CANDIDATE,
    CLAIMED_AT_ITS_LOCATION,
    CLAIMED_BY_NAME,
    EXTERNAL,
    RESOLVED,
    UNCLAIMED,
    ContextCensus,
    Declaration,
    Disagreement,
)
from julee.core.values.code_info import ClassInfo

pytestmark = pytest.mark.unit

CONTEXT = "src/acme/stories"


def a_class(file: str, name: str, line: int = 1) -> Declaration:
    return Declaration("acme.stories", name, CLASS, f"{CONTEXT}/{file}", line)


def joined(
    declarations: list[Declaration], **families: list[ClassInfo]
) -> ContextCensus:
    return census_of_context("stories", CONTEXT, declarations, families)


def state_of(census: ContextCensus, name: str) -> str:
    (membership,) = [m for m in census.memberships if m.declaration.name == name]
    return membership.state


class TestClaimedAtItsLocation:
    def test_a_family_member_claims_the_class_in_its_file(self) -> None:
        story = a_class("domain/models/story.py", "Story")

        census = joined([story], entities=[ClassInfo(name="Story", file="story.py")])

        (membership,) = census.memberships
        assert membership.state == CLAIMED_AT_ITS_LOCATION
        assert membership.families == ("entities",)

    def test_a_file_in_a_subdirectory_is_found(self) -> None:
        story = a_class("domain/models/planning/story.py", "Story")

        census = joined(
            [story], entities=[ClassInfo(name="Story", file="planning/story.py")]
        )

        assert state_of(census, "Story") == CLAIMED_AT_ITS_LOCATION

    def test_a_class_of_the_same_name_elsewhere_is_not_claimed(self) -> None:
        """The member names a file, and only the class there is the member."""
        census = joined(
            [
                a_class("domain/models/story.py", "Story"),
                a_class("infrastructure/story.py", "Story"),
            ],
            entities=[ClassInfo(name="Story", file="story.py")],
        )

        states = {m.declaration.file: m.state for m in census.memberships}
        assert states == {
            f"{CONTEXT}/domain/models/story.py": CLAIMED_AT_ITS_LOCATION,
            f"{CONTEXT}/infrastructure/story.py": UNCLAIMED,
        }

    def test_a_handler_still_in_services_is_found_there(self) -> None:
        """The parser reads it as a handler while it waits to be moved."""
        handler = a_class("domain/services/notify.py", "NotifyHandler")

        census = joined(
            [handler],
            handler_protocols=[ClassInfo(name="NotifyHandler", file="notify.py")],
        )

        assert state_of(census, "NotifyHandler") == CLAIMED_AT_ITS_LOCATION
        assert census.disagreements == ()

    def test_a_name_declared_twice_in_the_file_is_claimed_twice(self) -> None:
        """Two branches of an if: the member is whichever Python picks."""
        census = joined(
            [
                a_class("domain/models/story.py", "Story", line=2),
                a_class("domain/models/story.py", "Story", line=5),
            ],
            entities=[ClassInfo(name="Story", file="story.py")],
        )

        assert [m.state for m in census.memberships] == [CLAIMED_AT_ITS_LOCATION] * 2


class TestNameOnlyMembers:
    REQUEST = ClassInfo(name="PlanStoryRequest")

    def test_one_declaration_resolves_it(self) -> None:
        declared = a_class("dtos/story.py", "PlanStoryRequest")

        census = joined([declared], requests=[self.REQUEST])

        (member,) = census.name_only
        assert member.state == RESOLVED
        assert member.declarations == (declared,)
        assert state_of(census, "PlanStoryRequest") == CLAIMED_BY_NAME

    def test_several_declarations_leave_it_ambiguous(self) -> None:
        one = a_class("dtos/crud_story.py", "PlanStoryRequest")
        other = a_class("dtos/plan_story.py", "PlanStoryRequest")

        census = joined([one, other], requests=[self.REQUEST])

        (member,) = census.name_only
        assert member.state == AMBIGUOUS
        assert member.declarations == (one, other)

    def test_no_candidate_is_claimed(self) -> None:
        """Nothing says which was meant, so the census does not choose."""
        census = joined(
            [
                a_class("dtos/crud_story.py", "PlanStoryRequest"),
                a_class("dtos/plan_story.py", "PlanStoryRequest"),
            ],
            requests=[self.REQUEST],
        )

        assert [m.state for m in census.memberships] == [CANDIDATE, CANDIDATE]
        assert [m.families for m in census.memberships] == [("requests",)] * 2

    def test_no_declaration_in_the_context_makes_it_external(self) -> None:
        census = joined([], requests=[self.REQUEST])

        (member,) = census.name_only
        assert member.state == EXTERNAL
        assert member.declarations == ()

    def test_a_function_of_that_name_does_not_resolve_it(self) -> None:
        """A family member is a class."""
        function = Declaration(
            "acme.stories", "PlanStoryRequest", FUNCTION, f"{CONTEXT}/dtos/x.py", 1
        )

        census = joined([function], requests=[self.REQUEST])

        (member,) = census.name_only
        assert member.state == EXTERNAL
        assert state_of(census, "PlanStoryRequest") == UNCLAIMED

    def test_a_name_is_never_a_membership(self) -> None:
        """Only what the source declares appears among the declarations."""
        census = joined([], requests=[self.REQUEST])

        assert census.memberships == ()


class TestUnclaimed:
    def test_a_class_in_no_family_is_unclaimed(self) -> None:
        census = joined([a_class("infrastructure/memory.py", "MemoryStories")])

        (membership,) = census.memberships
        assert membership.state == UNCLAIMED
        assert membership.families == ()

    def test_one_in_a_family_directory_says_so(self) -> None:
        """The parser looked there and passed over it."""
        census = joined([a_class("usecases/plan.py", "StoryHelpers")])

        (membership,) = census.memberships
        assert membership.in_family_directory

    def test_one_elsewhere_says_so(self) -> None:
        census = joined([a_class("infrastructure/memory.py", "MemoryStories")])

        (membership,) = census.memberships
        assert not membership.in_family_directory

    def test_a_directory_that_only_starts_like_a_family_one_is_elsewhere(self) -> None:
        census = joined([a_class("usecases_old/plan.py", "Plan")])

        (membership,) = census.memberships
        assert not membership.in_family_directory

    @pytest.mark.parametrize("kind", [FUNCTION, BINDING])
    def test_no_family_holds_a_function_or_a_binding(self, kind: str) -> None:
        declared = Declaration(
            "acme.stories", "Story", kind, f"{CONTEXT}/domain/models/story.py", 1
        )

        census = joined([declared], entities=[ClassInfo(name="Story", file="story.py")])

        assert state_of(census, "Story") == UNCLAIMED


class TestWhenTheReadersDisagree:
    def test_a_member_whose_file_holds_no_such_class_is_a_disagreement(self) -> None:
        census = joined([], entities=[ClassInfo(name="Story", file="story.py")])

        assert census.disagreements == (
            Disagreement("entities", "Story", f"{CONTEXT}/domain/models/story.py"),
        )

    def test_a_class_of_that_name_in_another_file_does_not_settle_it(self) -> None:
        census = joined(
            [a_class("domain/models/tale.py", "Story")],
            entities=[ClassInfo(name="Story", file="story.py")],
        )

        assert len(census.disagreements) == 1
        assert state_of(census, "Story") == UNCLAIMED

    def test_an_unresolved_name_is_not_a_disagreement(self) -> None:
        """It is a fact about the source, not a fault in a reader."""
        census = joined([], requests=[ClassInfo(name="PlanStoryRequest")])

        assert census.disagreements == ()


class TestTheAccounting:
    def test_every_declaration_appears_once_in_file_and_line_order(self) -> None:
        declarations = [
            a_class("usecases/plan.py", "PlanStoryUseCase", line=9),
            a_class("domain/models/story.py", "Story", line=14),
            a_class("domain/models/story.py", "Tale", line=3),
        ]

        census = joined(declarations)

        assert [
            (m.declaration.file, m.declaration.line) for m in census.memberships
        ] == [
            (f"{CONTEXT}/domain/models/story.py", 3),
            (f"{CONTEXT}/domain/models/story.py", 14),
            (f"{CONTEXT}/usecases/plan.py", 9),
        ]

    def test_every_family_member_is_accounted_for(self) -> None:
        census = joined(
            [
                a_class("domain/models/story.py", "Story"),
                a_class("dtos/story.py", "PlanStoryRequest"),
            ],
            entities=[
                ClassInfo(name="Story", file="story.py"),
                ClassInfo(name="Lost", file="lost.py"),
            ],
            requests=[ClassInfo(name="PlanStoryRequest")],
            responses=[ClassInfo(name="PlanStoryResponse")],
        )

        located = sum(m.state == CLAIMED_AT_ITS_LOCATION for m in census.memberships)
        assert located + len(census.name_only) + len(census.disagreements) == 4


class TestTheFamilies:
    def test_every_family_of_a_bounded_context_has_its_directories(self) -> None:
        """A family the parser fills and this omits would go unjoined."""
        info = BoundedContextInfo(slug="stories")
        families = {
            name
            for name, value in vars(info).items()
            if isinstance(value, tuple) and name != "pipelines"
        }

        assert families == set(FAMILY_DIRECTORIES)

    def test_no_parser_result_means_empty_families(self) -> None:
        assert families_of(None) == dict.fromkeys(FAMILY_DIRECTORIES, ())

    def test_the_families_are_read_off_the_parser_result(self) -> None:
        story = ClassInfo(name="Story", file="story.py")

        families = families_of(BoundedContextInfo(slug="stories", entities=(story,)))

        assert families["entities"] == (story,)
