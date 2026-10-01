"""Tests for what `julee doctrine census` says and how it exits."""

import json
from pathlib import Path

import pytest

from julee.cli.census import STATEMENT, as_json, as_text, exit_status
from julee.cli.main import main
from julee.core.tests.census_solutions import a_solution, write
from julee.core.values.census import (
    AMBIGUOUS,
    CANDIDATE,
    CLAIMED_AT_ITS_LOCATION,
    EXTERNAL,
    UNCLAIMED,
    Census,
    ContextCensus,
    Declaration,
    Disagreement,
    Exclusion,
    Membership,
    NameOnlyMember,
    PassedOver,
)
from julee.core.values.code_info import UnreadableFile

pytestmark = pytest.mark.unit

STORY = Declaration(
    "acme.stories.domain.models.story",
    "Story",
    "class",
    "src/acme/stories/domain/models/story.py",
    14,
)
HELPERS = Declaration(
    "acme.stories.usecases.plan",
    "Helpers",
    "class",
    "src/acme/stories/usecases/plan.py",
    15,
)
MEMORY = Declaration(
    "acme.stories.infrastructure.memory",
    "MemoryStories",
    "class",
    "src/acme/stories/infrastructure/memory.py",
    4,
)
ONE = Declaration(
    "acme.stories.dtos.crud",
    "GetStoryRequest",
    "class",
    "src/acme/stories/dtos/crud.py",
    6,
)
OTHER = Declaration(
    "acme.stories.dtos.get",
    "GetStoryRequest",
    "class",
    "src/acme/stories/dtos/get.py",
    6,
)

STORIES = ContextCensus(
    slug="stories",
    path="src/acme/stories",
    memberships=(
        Membership(STORY, CLAIMED_AT_ITS_LOCATION, ("entities",), True),
        Membership(ONE, CANDIDATE, ("requests",)),
        Membership(OTHER, CANDIDATE, ("requests",)),
        Membership(MEMORY, UNCLAIMED),
        Membership(HELPERS, UNCLAIMED, (), True),
    ),
    name_only=(
        NameOnlyMember("requests", "GetStoryRequest", AMBIGUOUS, (ONE, OTHER)),
        NameOnlyMember("responses", "ArchiveStoryResponse", EXTERNAL),
    ),
)


def a_census(**changes: object) -> Census:
    return Census(
        **{  # type: ignore[arg-type]
            "search_root": "src/acme",
            "files_read": 12,
            "test_files_excluded": 1,
            "contexts": (STORIES,),
            **changes,
        }
    )


def flat(text: str) -> str:
    """The text with its line breaks and indents taken out."""
    return " ".join(text.split())


# =============================================================================
# How it exits
# =============================================================================


class TestTheExitStatus:
    def test_a_complete_census_whose_readers_agree_is_0(self) -> None:
        assert exit_status(a_census()) == 0

    def test_unclaimed_declarations_do_not_change_it(self) -> None:
        """Whether one is a fault is a rule's question."""
        assert any(m.state == UNCLAIMED for m in STORIES.memberships)
        assert exit_status(a_census()) == 0

    def test_ambiguous_and_external_names_do_not_change_it(self) -> None:
        assert {member.state for member in STORIES.name_only} == {AMBIGUOUS, EXTERNAL}
        assert exit_status(a_census()) == 0

    def test_a_file_that_could_not_be_read_is_1(self) -> None:
        unreadable = (UnreadableFile("src/acme/stories/x.py", "Syntax error"),)

        assert exit_status(a_census(unreadable=unreadable)) == 1

    def test_readers_that_disagree_are_1(self) -> None:
        disagreeing = ContextCensus(
            slug="stories",
            path="src/acme/stories",
            disagreements=(
                Disagreement(
                    "entities", "Story", "src/acme/stories/domain/models/story.py"
                ),
            ),
        )

        assert exit_status(a_census(contexts=(disagreeing,))) == 1


# =============================================================================
# What the text says
# =============================================================================


class TestTheText:
    def test_it_says_what_the_census_reports_and_does_not(self) -> None:
        assert STATEMENT in flat(as_text(a_census()))

    def test_the_statement_distinguishes_membership_from_rule_coverage(self) -> None:
        assert "does not report which doctrine rules check" in STATEMENT
        assert "not unchecked" in STATEMENT
        assert "not compliant" in STATEMENT

    def test_it_gives_the_scope(self) -> None:
        assert "Scope: 12 files read, 1 test file excluded." in as_text(a_census())

    def test_it_names_each_exclusion_with_its_reason(self) -> None:
        text = as_text(
            a_census(exclusions=(Exclusion("src/acme/.cache", "hidden directory"),))
        )

        assert "Excluded: src/acme/.cache (hidden directory)" in text

    def test_it_names_an_unreadable_file_and_says_the_census_is_incomplete(
        self,
    ) -> None:
        text = as_text(
            a_census(
                unreadable=(
                    UnreadableFile(
                        "src/acme/stories/x.py", "Syntax error: invalid syntax (line 8)"
                    ),
                )
            )
        )

        assert (
            "Unreadable: src/acme/stories/x.py: Syntax error: invalid syntax (line 8)"
            in text
        )
        assert "The census is incomplete: 1 file in scope could not be read." in text

    def test_a_complete_census_does_not_say_it_is_incomplete(self) -> None:
        assert "incomplete" not in as_text(a_census())

    def test_it_counts_each_kind_by_state(self) -> None:
        assert (
            "  class: 1 claimed at its location, 2 candidate, 2 unclaimed"
            in as_text(a_census())
        )

    def test_it_lists_an_ambiguous_name_with_its_candidates(self) -> None:
        lines = as_text(a_census()).splitlines()
        start = lines.index("    requests GetStoryRequest: ambiguous")

        assert lines[start + 1 : start + 3] == [
            "      src/acme/stories/dtos/crud.py:6",
            "      src/acme/stories/dtos/get.py:6",
        ]

    def test_it_lists_an_external_name_with_nothing_under_it(self) -> None:
        assert "    responses ArchiveStoryResponse: external" in as_text(a_census())

    def test_what_is_unclaimed_in_a_family_directory_comes_first(self) -> None:
        text = as_text(a_census())

        assert text.index("Unclaimed in a family directory:") < text.index(
            "Unclaimed elsewhere:"
        )
        assert "    src/acme/stories/usecases/plan.py:15 class Helpers" in text
        assert (
            "    src/acme/stories/infrastructure/memory.py:4 class MemoryStories"
            in text
        )

    def test_a_claimed_declaration_is_counted_and_not_listed(self) -> None:
        assert "class Story" not in as_text(a_census())

    def test_it_reports_a_disagreement(self) -> None:
        disagreeing = ContextCensus(
            slug="stories",
            path="src/acme/stories",
            disagreements=(
                Disagreement(
                    "entities", "Story", "src/acme/stories/domain/models/story.py"
                ),
            ),
        )

        text = as_text(a_census(contexts=(disagreeing,)))

        assert "The readers disagree" in text
        assert "entities holds Story at src/acme/stories/domain/models/story.py" in text

    def test_it_lists_source_in_no_bounded_context_with_the_reason(self) -> None:
        helper = Declaration(
            "acme.tools.helper", "Helper", "class", "src/acme/tools/helper.py", 4
        )
        text = as_text(
            a_census(
                passed_over=(PassedOver("src/acme/tools", "no markers", (helper,)),)
            )
        )

        assert "In no bounded context:\n  src/acme/tools (no markers)\n" in text
        assert "    src/acme/tools/helper.py:4 class Helper" in text


# =============================================================================
# What the JSON says
# =============================================================================


class TestTheJson:
    def test_it_carries_the_same_statement(self) -> None:
        assert json.loads(as_json(a_census()))["census"] == STATEMENT

    def test_it_gives_the_scope_and_whether_the_census_can_be_relied_on(self) -> None:
        document = json.loads(
            as_json(
                a_census(exclusions=(Exclusion("src/acme/.cache", "hidden directory"),))
            )
        )

        assert document["complete"] is True
        assert document["readers_agree"] is True
        assert document["scope"] == {
            "files_read": 12,
            "test_files_excluded": 1,
            "excluded": [{"path": "src/acme/.cache", "reason": "hidden directory"}],
            "unreadable": [],
        }

    def test_it_carries_every_declaration_claimed_or_not(self) -> None:
        (stories,) = json.loads(as_json(a_census()))["contexts"]

        assert stories["declarations"][0] == {
            "identity": "acme.stories.domain.models.story:Story",
            "kind": "class",
            "file": "src/acme/stories/domain/models/story.py",
            "line": 14,
            "state": "claimed at its location",
            "families": ["entities"],
            "in_family_directory": True,
        }
        assert len(stories["declarations"]) == 5

    def test_it_carries_each_name_only_member_with_its_declarations(self) -> None:
        (stories,) = json.loads(as_json(a_census()))["contexts"]

        assert [
            (member["name"], member["state"], len(member["declarations"]))
            for member in stories["name_only_members"]
        ] == [
            ("GetStoryRequest", "ambiguous", 2),
            ("ArchiveStoryResponse", "external", 0),
        ]


# =============================================================================
# The command, against a solution on disk
# =============================================================================


class TestTheCommand:
    @pytest.fixture
    def solution(self, tmp_path: Path) -> Path:
        return a_solution(tmp_path / "acme")

    def test_it_prints_the_census_and_exits_0(
        self, solution: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        status = main(["doctrine", "census", "--target", str(solution)])

        printed = capsys.readouterr().out
        assert status == 0
        assert printed.startswith("census: search_root src/acme\n")
        assert "stories (src/acme/stories)" in printed

    def test_json_is_a_document(
        self, solution: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        status = main(
            ["doctrine", "census", "--target", str(solution), "--format", "json"]
        )

        document = json.loads(capsys.readouterr().out)
        assert status == 0
        assert [context["slug"] for context in document["contexts"]] == [
            "engagements",
            "stories",
        ]

    def test_an_unreadable_file_makes_it_exit_1_and_still_print(
        self, solution: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        write(
            solution / "src/acme/stories",
            {"domain/values/orphan.py": "class Orphan:\n    pass\n\n\ndef broken(:\n"},
        )

        status = main(["doctrine", "census", "--target", str(solution)])

        printed = capsys.readouterr().out
        assert status == 1
        assert "Unreadable: src/acme/stories/domain/values/orphan.py" in printed
        assert "stories (src/acme/stories)" in printed

    def test_a_target_that_is_no_solution_makes_it_exit_2(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        status = main(["doctrine", "census", "--target", str(tmp_path)])

        captured = capsys.readouterr()
        assert status == 2
        assert captured.out == ""
        assert "error:" in captured.err

    @pytest.mark.parametrize("form", ["text", "json"])
    def test_two_runs_give_the_same_bytes(
        self, solution: Path, capsys: pytest.CaptureFixture[str], form: str
    ) -> None:
        arguments = ["doctrine", "census", "--target", str(solution), "--format", form]

        main(arguments)
        first = capsys.readouterr().out
        main(arguments)

        assert capsys.readouterr().out == first

    @pytest.mark.parametrize("form", ["text", "json"])
    def test_no_path_in_the_report_is_absolute(
        self, solution: Path, capsys: pytest.CaptureFixture[str], form: str
    ) -> None:
        """So the same source gives the same report wherever it is checked out."""
        main(["doctrine", "census", "--target", str(solution), "--format", form])

        assert str(solution) not in capsys.readouterr().out
