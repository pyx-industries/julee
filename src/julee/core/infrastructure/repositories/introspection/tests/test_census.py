"""Tests for taking a census of a solution on disk.

Every expected result is written here from the fixture sources in
:mod:`julee.core.tests.census_solutions`, line numbers included. None
is taken from the code under test.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)
from julee.core.infrastructure.repositories.introspection.census import take_census
from julee.core.parsers.ast import parse_bounded_context
from julee.core.tests.census_solutions import SEARCH_ROOT, a_solution, write
from julee.core.values.census import (
    AMBIGUOUS,
    CLAIMED_AT_ITS_LOCATION,
    EXTERNAL,
    RESOLVED,
    UNCLAIMED,
    Census,
    ContextCensus,
    Exclusion,
    Membership,
)

pytestmark = pytest.mark.unit

STORIES = "src/acme/stories"
ENGAGEMENTS = "src/acme/engagements"

DOES_NOT_PARSE = '''"""Half written."""


class Orphan:
    """Nothing imports this yet."""


def broken(:
'''


def census_of(root: Path) -> Census:
    return take_census(
        root, SEARCH_ROOT, FilesystemBoundedContextRepository(root, SEARCH_ROOT)
    )


def context(census: Census, slug: str) -> ContextCensus:
    (found,) = [each for each in census.contexts if each.slug == slug]
    return found


def rows(found: ContextCensus) -> list[tuple[str, int, str, str, str]]:
    """Each declaration as file within the context, line, kind, name, state."""
    return [
        (
            m.declaration.file.removeprefix(found.path + "/"),
            m.declaration.line,
            m.declaration.kind,
            m.declaration.name,
            m.state,
        )
        for m in found.memberships
    ]


@pytest.fixture(autouse=True)
def no_enclosing_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run as though no git process had started the tests.

    A git hook, and ``git rebase --exec``, export ``GIT_DIR`` to what
    they run. Git then acts on that repository whatever directory it is
    run in, so a test that runs ``git init`` in its own directory would
    reinitialise the repository the tests were started from, and mark
    it bare.
    """
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_NAMESPACE",
        "GIT_PREFIX",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def solution(tmp_path: Path) -> Path:
    return a_solution(tmp_path / "acme")


class TestAContextLaidOutAsPrescribed:
    def test_every_declaration_is_located_with_its_state(self, solution: Path) -> None:
        assert rows(context(census_of(solution), "stories")) == [
            ("domain/models/_draft.py", 4, "class", "Draft", CLAIMED_AT_ITS_LOCATION),
            ("domain/models/story.py", 6, "binding", "StoryId", UNCLAIMED),
            ("domain/models/story.py", 9, "function", "new_story_id", UNCLAIMED),
            ("domain/models/story.py", 14, "class", "Story", CLAIMED_AT_ITS_LOCATION),
            (
                "domain/repositories/story.py",
                6,
                "class",
                "StoryRepository",
                CLAIMED_AT_ITS_LOCATION,
            ),
            ("domain/values/score.py", 7, "class", "Score", CLAIMED_AT_ITS_LOCATION),
            (
                "dtos/crud_story.py",
                6,
                "class",
                "GetStoryRequest",
                CLAIMED_AT_ITS_LOCATION,
            ),
            (
                "dtos/get_story.py",
                6,
                "class",
                "GetStoryRequest",
                CLAIMED_AT_ITS_LOCATION,
            ),
            ("dtos/story.py", 6, "class", "PlanStoryRequest", CLAIMED_AT_ITS_LOCATION),
            (
                "dtos/story.py",
                10,
                "class",
                "PlanStoryResponse",
                CLAIMED_AT_ITS_LOCATION,
            ),
            ("dtos/story.py", 14, "class", "StoryMessage", CLAIMED_AT_ITS_LOCATION),
            (
                "infrastructure/memory.py",
                4,
                "class",
                "MemoryStoryRepository",
                UNCLAIMED,
            ),
            (
                "usecases/plan_story.py",
                8,
                "class",
                "PlanStoryUseCase",
                CLAIMED_AT_ITS_LOCATION,
            ),
            (
                "usecases/plan_story.py",
                15,
                "class",
                "StoryHelpers",
                CLAIMED_AT_ITS_LOCATION,
            ),
            (
                "usecases/plan_story.py",
                19,
                "class",
                "TestDouble",
                CLAIMED_AT_ITS_LOCATION,
            ),
        ]

    def test_a_declaration_carries_its_module_and_its_path_from_the_root(
        self, solution: Path
    ) -> None:
        stories = context(census_of(solution), "stories")
        (story,) = [
            m.declaration for m in stories.memberships if m.declaration.name == "Story"
        ]

        assert story.identity == "acme.stories.domain.models.story:Story"
        assert story.file == "src/acme/stories/domain/models/story.py"

    def test_each_claim_names_its_family(self, solution: Path) -> None:
        stories = context(census_of(solution), "stories")
        families = {
            m.declaration.name: m.families for m in stories.memberships if m.families
        }

        assert families == {
            "Draft": ("entities",),
            "Story": ("entities",),
            "StoryRepository": ("repository_protocols",),
            "Score": ("values",),
            "GetStoryRequest": ("dtos",),
            "PlanStoryRequest": ("dtos",),
            "PlanStoryResponse": ("dtos",),
            "StoryMessage": ("dtos",),
            "PlanStoryUseCase": ("use_cases",),
            "StoryHelpers": ("use_cases",),
            "TestDouble": ("use_cases",),
        }

    def test_the_names_a_use_case_file_imports_are_resolved_or_said_not_to_be(
        self, solution: Path
    ) -> None:
        stories = context(census_of(solution), "stories")

        assert [
            (
                member.family,
                member.name,
                member.state,
                [f"{found.file}:{found.line}" for found in member.declarations],
            )
            for member in stories.name_only
        ] == [
            (
                "requests",
                "GetStoryRequest",
                AMBIGUOUS,
                [
                    f"{STORIES}/dtos/crud_story.py:6",
                    f"{STORIES}/dtos/get_story.py:6",
                ],
            ),
            ("requests", "PlanStoryRequest", RESOLVED, [f"{STORIES}/dtos/story.py:6"]),
            ("responses", "ArchiveStoryResponse", EXTERNAL, []),
            (
                "responses",
                "PlanStoryResponse",
                RESOLVED,
                [f"{STORIES}/dtos/story.py:10"],
            ),
        ]

    def test_what_the_parser_passed_over_in_a_family_directory_says_so(
        self, solution: Path
    ) -> None:
        """A function and a binding, which no family holds. No class is
        among them: one named like a test or in an underscore module is
        read like any other (ADR 021), and one in usecases/ is a use
        case whatever it is called (ADR 020)."""
        stories = context(census_of(solution), "stories")

        assert {
            m.declaration.name
            for m in stories.memberships
            if m.state == UNCLAIMED and m.in_family_directory
        } == {"StoryId", "new_story_id"}

    def test_the_readers_agree(self, solution: Path) -> None:
        census = census_of(solution)

        assert census.readers_agree
        assert all(found.disagreements == () for found in census.contexts)


class TestAContextWithAnArea:
    def test_everything_is_located_and_what_a_family_reads_is_claimed(
        self, solution: Path
    ) -> None:
        """The area's entity and repository are claimed where they sit
        (ADR 023). The port outside domain/ is in no family."""
        assert rows(context(census_of(solution), "engagements")) == [
            (
                "domain/engagement/engagement.py",
                6,
                "binding",
                "EngagementId",
                UNCLAIMED,
            ),
            (
                "domain/engagement/engagement.py",
                10,
                "class",
                "Engagement",
                CLAIMED_AT_ITS_LOCATION,
            ),
            (
                "domain/engagement/repositories/engagement.py",
                6,
                "class",
                "EngagementRepository",
                CLAIMED_AT_ITS_LOCATION,
            ),
            ("ports/clock.py", 6, "class", "ClockService", UNCLAIMED),
            (
                "usecases/engagement.py",
                4,
                "class",
                "BaseEngagementUseCase",
                CLAIMED_AT_ITS_LOCATION,
            ),
            (
                "usecases/engagement.py",
                11,
                "class",
                "RecordEngagement",
                CLAIMED_AT_ITS_LOCATION,
            ),
            (
                "usecases/engagement.py",
                15,
                "class",
                "GetEngagement",
                CLAIMED_AT_ITS_LOCATION,
            ),
            (
                "usecases/engagement.py",
                19,
                "class",
                "SearchEngagements",
                CLAIMED_AT_ITS_LOCATION,
            ),
            (
                "usecases/engagement.py",
                23,
                "class",
                "ListEngagementFilters",
                CLAIMED_AT_ITS_LOCATION,
            ),
        ]

    def test_a_class_read_in_an_area_says_which_area(self, solution: Path) -> None:
        """Its file is counted from domain/, where the area's name begins."""
        info = parse_bounded_context(solution / ENGAGEMENTS)
        assert info is not None

        assert [(found.name, found.file) for found in info.entities] == [
            ("Engagement", "engagement/engagement.py")
        ]
        assert [(found.name, found.file) for found in info.repository_protocols] == [
            ("EngagementRepository", "engagement/repositories/engagement.py")
        ]

    def test_each_claim_names_its_family(self, solution: Path) -> None:
        families = {
            m.declaration.name: m.families
            for m in context(census_of(solution), "engagements").memberships
            if m.state == CLAIMED_AT_ITS_LOCATION and "domain/" in m.declaration.file
        }

        assert families == {
            "Engagement": ("entities",),
            "EngagementRepository": ("repository_protocols",),
        }

    def test_what_an_area_holds_besides_classes_is_passed_over_and_says_so(
        self, solution: Path
    ) -> None:
        engagements = context(census_of(solution), "engagements")

        assert {
            m.declaration.name
            for m in engagements.memberships
            if m.state == UNCLAIMED and m.in_family_directory
        } == {"EngagementId"}

    def test_a_port_outside_domain_is_in_no_family(self, solution: Path) -> None:
        engagements = context(census_of(solution), "engagements")
        (clock,) = [
            m for m in engagements.memberships if m.declaration.name == "ClockService"
        ]

        assert clock.state == UNCLAIMED
        assert not clock.in_family_directory

    def test_the_readers_agree(self, solution: Path) -> None:
        assert context(census_of(solution), "engagements").disagreements == ()


class TestSourceInNoBoundedContext:
    def test_each_directory_is_listed_with_discoverys_reason(
        self, solution: Path
    ) -> None:
        assert [
            (
                passed.path,
                passed.reason,
                [
                    (found.file, found.line, found.kind, found.name)
                    for found in passed.declarations
                ],
            )
            for passed in census_of(solution).passed_over
        ] == [
            (
                "src/acme/scripts",
                "not a Python package",
                [("src/acme/scripts/run.py", 4, "function", "main")],
            ),
            (
                "src/acme/shared",
                "a reserved name",
                [("src/acme/shared/util.py", 4, "function", "slugify")],
            ),
            (
                "src/acme/tools",
                "no module under domain is read as entities, and usecases holds no Python",
                [("src/acme/tools/helper.py", 4, "class", "Helper")],
            ),
        ]

    def test_a_declaration_beside_the_contexts_is_listed_under_the_search_root(
        self, solution: Path
    ) -> None:
        (solution / SEARCH_ROOT / "__init__.py").write_text("class Acme:\n    pass\n")

        first = census_of(solution).passed_over[0]

        assert first.path == SEARCH_ROOT
        assert [found.name for found in first.declarations] == ["Acme"]


class TestScope:
    def test_the_files_read_and_the_tests_left_out_are_counted(
        self, solution: Path
    ) -> None:
        """33 modules and package files; a test module and its package."""
        census = census_of(solution)

        assert census.files_read == 33
        assert census.test_files_excluded == 2
        assert census.exclusions == ()
        assert census.is_complete

    def test_a_test_file_is_not_read(self, solution: Path) -> None:
        names = {
            m.declaration.name
            for found in census_of(solution).contexts
            for m in found.memberships
        }

        assert "TestStory" not in names

    def test_a_hidden_directory_is_not_read_and_is_named(self, solution: Path) -> None:
        write(
            solution / SEARCH_ROOT, {".cache/generated.py": "class Cached:\n    pass\n"}
        )

        census = census_of(solution)

        assert census.exclusions == (Exclusion("src/acme/.cache", "hidden directory"),)
        assert census.files_read == 33

    def test_a_hidden_directory_holding_no_python_is_not_named(
        self, solution: Path
    ) -> None:
        """Leaving it out removed nothing from scope."""
        write(solution / SEARCH_ROOT, {".cache/notes.txt": "nothing to read"})

        assert census_of(solution).exclusions == ()

    @pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
    def test_what_git_ignores_is_not_read_and_is_named(self, solution: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=solution, check=True)
        (solution / ".gitignore").write_text("generated/\n")
        write(solution / STORIES, {"generated/out.py": "class Generated:\n    pass\n"})

        census = census_of(solution)

        assert census.exclusions == (
            Exclusion("src/acme/stories/generated", "git-ignored"),
        )
        assert census.files_read == 33

    @pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
    def test_a_single_ignored_file_is_named_itself(self, solution: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=solution, check=True)
        (solution / ".gitignore").write_text("local_settings.py\n")
        write(solution / STORIES, {"local_settings.py": "class Local:\n    pass\n"})

        assert census_of(solution).exclusions == (
            Exclusion("src/acme/stories/local_settings.py", "git-ignored"),
        )

    def test_outside_a_repository_nothing_is_ignored(self, solution: Path) -> None:
        (solution / ".gitignore").write_text("stories/\n")

        assert census_of(solution).files_read == 33


class TestSourceThatCannotBeRead:
    def test_a_file_nothing_imports_is_listed_with_its_error(
        self, solution: Path
    ) -> None:
        write(solution / STORIES, {"domain/values/orphan.py": DOES_NOT_PARSE})

        census = census_of(solution)

        (found,) = census.unreadable
        assert found.file == "src/acme/stories/domain/values/orphan.py"
        assert "line 8" in found.problem
        assert not census.is_complete

    def test_the_rest_is_still_reported(self, solution: Path) -> None:
        write(solution / STORIES, {"domain/values/orphan.py": DOES_NOT_PARSE})

        stories = context(census_of(solution), "stories")

        assert len(stories.memberships) == 15

    def test_one_outside_every_context_is_listed_too(self, solution: Path) -> None:
        write(solution / SEARCH_ROOT, {"tools/orphan.py": DOES_NOT_PARSE})

        (found,) = census_of(solution).unreadable

        assert found.file == "src/acme/tools/orphan.py"

    def test_a_file_that_is_not_utf8_is_listed(self, solution: Path) -> None:
        (solution / STORIES / "latin.py").write_bytes(b'x = "\xff\xfe"\n')

        (found,) = census_of(solution).unreadable

        assert found.file == "src/acme/stories/latin.py"

    def test_an_unreadable_test_file_is_out_of_scope(self, solution: Path) -> None:
        write(solution / STORIES, {"tests/test_orphan.py": DOES_NOT_PARSE})

        assert census_of(solution).is_complete


class TestNothingIsImported:
    def test_a_module_that_raises_on_import_is_read(self, solution: Path) -> None:
        write(
            solution / STORIES,
            {
                "domain/values/explosive.py": (
                    'raise RuntimeError("this module was imported")\n\n\n'
                    "class Explosive:\n    pass\n"
                )
            },
        )

        stories = context(census_of(solution), "stories")

        assert (
            "domain/values/explosive.py",
            4,
            "class",
            "Explosive",
            CLAIMED_AT_ITS_LOCATION,
        ) in rows(stories)


class TestAMove:
    @staticmethod
    def story_moved_to(solution: Path, *directory: str) -> Membership:
        """Move the Story entity's module and find it in the census again."""
        destination = (solution / STORIES).joinpath(*directory)
        destination.mkdir(parents=True, exist_ok=True)
        (solution / STORIES / "domain" / "models" / "story.py").rename(
            destination / "story.py"
        )
        stories = context(census_of(solution), "stories")
        (story,) = [m for m in stories.memberships if m.declaration.name == "Story"]
        return story

    def test_an_entity_moved_out_of_domain_is_unclaimed_where_it_went(
        self, solution: Path
    ) -> None:
        """Gone from its family, and still on the page."""
        story = self.story_moved_to(solution, "things")

        assert story.declaration.file == "src/acme/stories/things/story.py"
        assert story.state == UNCLAIMED
        assert not story.in_family_directory

    def test_an_entity_moved_into_an_area_is_still_an_entity(
        self, solution: Path
    ) -> None:
        """A directory under domain/ that is no kind's is an area (ADR 023)."""
        story = self.story_moved_to(solution, "domain", "things")

        assert story.declaration.file == "src/acme/stories/domain/things/story.py"
        assert story.state == CLAIMED_AT_ITS_LOCATION
        assert story.families == ("entities",)

    def test_an_entity_moved_directly_under_domain_is_still_an_entity(
        self, solution: Path
    ) -> None:
        """A module domain/ holds itself is read as entities (ADR 024)."""
        story = self.story_moved_to(solution, "domain")

        assert story.declaration.file == "src/acme/stories/domain/story.py"
        assert story.state == CLAIMED_AT_ITS_LOCATION
        assert story.families == ("entities",)


class TestTheSameSourceGivesTheSameCensus:
    def test_two_censuses_are_equal(self, solution: Path) -> None:
        assert census_of(solution) == census_of(solution)

    def test_contexts_and_declarations_are_ordered_by_path_and_line(
        self, solution: Path
    ) -> None:
        census = census_of(solution)

        assert [found.path for found in census.contexts] == [ENGAGEMENTS, STORIES]
        for found in census.contexts:
            keys = [(m.declaration.file, m.declaration.line) for m in found.memberships]
            assert keys == sorted(keys)
