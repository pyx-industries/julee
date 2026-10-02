"""Message identity rules over actual source and the census's readers."""

from pathlib import Path

import pytest

from julee.core.doctrine.resolution import Verdict
from julee.core.doctrine.rules.messages import (
    ambiguous_message_names,
    classes_in_dtos_that_are_not_messages,
)
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)
from julee.core.infrastructure.repositories.introspection.census import take_census
from julee.core.tests.census_solutions import write

pytestmark = pytest.mark.unit
SEARCH_ROOT = "src/acme"


def context(root: Path, slug: str, files: dict[str, str]) -> None:
    """Write a context and its message imports without importing the source."""
    write(root / SEARCH_ROOT / slug, {"__init__.py": "", **files})


def objections(root: Path) -> list[str]:
    repo = FilesystemBoundedContextRepository(root, SEARCH_ROOT)
    census = take_census(root, SEARCH_ROOT, repo)
    assert census.unreadable == ()
    assert all(not found.disagreements for found in census.contexts)
    assert census.is_complete and census.readers_agree
    return ambiguous_message_names(census.contexts)


@pytest.mark.parametrize("name", ["GetStoryRequest", "GetStoryResponse"])
def test_two_message_declarations_name_both_locations(
    tmp_path: Path, name: str
) -> None:
    context(
        tmp_path,
        "stories",
        {
            "usecases/get.py": f"from acme.stories.dtos.first import {name}\n",
            "dtos/first.py": f"class {name}: pass\n",
            "dtos/second.py": f"class {name}: pass\n",
        },
    )
    (objection,) = objections(tmp_path)
    assert f"stories.{name}" in objection
    assert "src/acme/stories/dtos/first.py:1" in objection
    assert "src/acme/stories/dtos/second.py:1" in objection


def test_repeated_imports_and_reexports_of_one_message_are_allowed(
    tmp_path: Path,
) -> None:
    context(
        tmp_path,
        "stories",
        {
            "dtos/message.py": "class SharedRequest: pass\n",
            "dtos/__init__.py": "from .message import SharedRequest\n",
            "usecases/first.py": "from acme.stories.dtos import SharedRequest\n",
            "usecases/second.py": "from acme.stories.dtos.message import SharedRequest\n",
        },
    )
    assert objections(tmp_path) == []


def test_the_same_message_name_in_separate_contexts_is_allowed(tmp_path: Path) -> None:
    for slug in ("stories", "plans"):
        context(tmp_path, slug, {"usecases/get.py": "class GetRequest: pass\n"})
    assert objections(tmp_path) == []


def test_two_messages_declared_in_usecase_files_are_not_hidden_by_locations(
    tmp_path: Path,
) -> None:
    context(
        tmp_path,
        "stories",
        {
            "usecases/first.py": "class GetRequest: pass\n",
            "usecases/second.py": "class GetRequest: pass\n",
        },
    )
    assert len(objections(tmp_path)) == 1


def test_conditional_declarations_of_one_name_remain_distinct(tmp_path: Path) -> None:
    context(
        tmp_path,
        "stories",
        {
            "usecases/get.py": "from acme.stories.dtos.message import GetRequest\n",
            "dtos/message.py": "if True:\n    class GetRequest: pass\nelse:\n    class GetRequest: pass\n",
        },
    )
    (objection,) = objections(tmp_path)
    assert "message.py:2" in objection
    assert "message.py:4" in objection


def test_external_names_and_nonclass_names_are_not_new_objections(
    tmp_path: Path,
) -> None:
    context(
        tmp_path,
        "stories",
        {
            "usecases/get.py": "from elsewhere import ExternalRequest\nfrom acme.stories.dtos.message import GetRequest\n",
            "dtos/message.py": "class GetRequest: pass\n",
            "tools.py": "def GetRequest(): pass\n",
        },
    )
    assert objections(tmp_path) == []


def test_duplicates_not_in_message_families_are_outside_this_rule(
    tmp_path: Path,
) -> None:
    context(
        tmp_path,
        "stories",
        {
            "usecases/get.py": "class GetUseCase: pass\n",
            "dtos/first.py": "class OtherRequest: pass\n",
            "dtos/second.py": "class OtherRequest: pass\n",
        },
    )
    assert objections(tmp_path) == []


class TestClassesInDtosThatAreNotMessages:
    """A class in dtos/ is a pydantic model, or an enum one of them uses."""

    def test_a_class_with_nothing_against_it_is_allowed(self) -> None:
        verdicts = [Verdict("stories", "StoryMessage", None)]

        assert classes_in_dtos_that_are_not_messages(verdicts) == []

    def test_a_class_with_a_reason_is_reported(self) -> None:
        verdicts = [Verdict("stories", "StoryMessage", "it is not a BaseModel")]

        assert classes_in_dtos_that_are_not_messages(verdicts)

    def test_the_objection_names_the_context_the_class_and_the_reason(self) -> None:
        (objection,) = classes_in_dtos_that_are_not_messages(
            [Verdict("stories", "StoryMessage", "it is not a BaseModel")]
        )

        assert objection.startswith("stories.StoryMessage: ")
        assert "it is not a BaseModel" in objection

    def test_the_objection_says_what_dtos_is_for(self) -> None:
        """So the author knows whether to change the class or move it."""
        (objection,) = classes_in_dtos_that_are_not_messages(
            [Verdict("stories", "StoryMessage", "it is not a BaseModel")]
        )

        assert "pydantic model" in objection
        assert "enum" in objection

    def test_only_the_offenders_are_reported(self) -> None:
        verdicts = [
            Verdict("stories", "PlanStoryRequest", None),
            Verdict("stories", "StoryMessage", "it is not a BaseModel"),
            Verdict("stories", "StoryState", None),
        ]

        assert len(classes_in_dtos_that_are_not_messages(verdicts)) == 1
