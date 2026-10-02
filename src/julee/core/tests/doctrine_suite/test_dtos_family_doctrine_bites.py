"""What doctrine does with a class in dtos/, run against real solutions.

A class in dtos/ is a message (ADR 022), found by where it sits, and a
message is a pydantic model. Until that, a class there was read only if
a use case imported it by a name ending in Request or Response.

The cases that were silent are the ones tested hardest: a class nothing
imports, and a class that is neither a request nor a response.
"""

import subprocess
from pathlib import Path

import pytest

from .harness import a_julee_solution, assert_doctrine_ran, run_doctrine

pytestmark = pytest.mark.unit

MESSAGES_TEST = "src/julee/core/doctrine/test_messages.py"
DTOS_SELECTOR = "pydantic_model_or_an_enum"
EXPECTED_TESTS = 1

ENTITY = '''"""The Story entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    """A unit of work."""

    slug: str
'''

DTOS = '''"""The messages planning a story takes and returns."""

from pydantic import BaseModel


class PlanStoryRequest(BaseModel):
    """Which story to plan."""

    slug: str


class PlanStoryResponse(BaseModel):
    """The story as planned."""

    slug: str
'''

A_USE_CASE = '''"""Planning a story."""

from ..dtos.plan_story import PlanStoryRequest, PlanStoryResponse


class PlanStoryUseCase:
    """Plans a story."""

    async def execute(self, request: PlanStoryRequest) -> PlanStoryResponse:
        return PlanStoryResponse(slug=request.slug)
'''

A_PLAIN_CLASS = '''"""Something in dtos that is not a pydantic model."""


class {name}:
    """Validated by nothing."""

    slug: str
'''

A_NESTED_MESSAGE = '''"""A message another message is built from."""

from enum import StrEnum

from pydantic import BaseModel


class StoryState(StrEnum):
    """The states a story message may report."""

    DRAFT = "draft"
    PLANNED = "planned"


class StoryMessage(BaseModel):
    """A story on the wire."""

    slug: str
    state: StoryState


class DetailedStoryMessage(StoryMessage):
    """A story on the wire, with more said about it."""

    notes: str
'''

A_PYDANTIC_DATACLASS = '''"""A dataclass that validates."""

from pydantic.dataclasses import dataclass


@dataclass
class StoryMessage:
    """Reads as a plain dataclass everywhere else."""

    slug: str
'''


def a_solution(root: Path) -> Path:
    """Write a solution with one entity, one use case and its messages.

    Args:
        root: The solution root to write into

    Returns:
        The bounded context directory, for the caller to add to
    """
    context = a_julee_solution(root)
    for package in ("domain", "domain/models", "dtos", "usecases"):
        (context / package).mkdir(parents=True)
        (context / package / "__init__.py").write_text("")
    (context / "domain" / "models" / "story.py").write_text(ENTITY)
    (context / "dtos" / "plan_story.py").write_text(DTOS)
    (context / "usecases" / "plan_story.py").write_text(A_USE_CASE)
    return context


def objects(result: subprocess.CompletedProcess[str]) -> bool:
    return result.returncode != 0


def test_pydantic_messages_are_not_objected_to(tmp_path: Path) -> None:
    root = tmp_path / "messages"
    a_solution(root)

    result = run_doctrine(root, MESSAGES_TEST, DTOS_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, DTOS_SELECTOR)
    assert not objects(result), (
        "doctrine objected to pydantic messages in dtos/:\n" + result.stdout
    )


def test_a_request_nothing_imports_is_objected_to(tmp_path: Path) -> None:
    """Half written, and read by nothing while an import was what made a
    class in dtos/ visible."""
    root = tmp_path / "unimported"
    context = a_solution(root)
    (context / "dtos" / "archive_story.py").write_text(
        A_PLAIN_CLASS.format(name="ArchiveStoryRequest")
    )

    result = run_doctrine(root, MESSAGES_TEST, DTOS_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, DTOS_SELECTOR)
    assert objects(result), (
        "doctrine passed over a request that is not a pydantic model:\n" + result.stdout
    )
    assert "stories.ArchiveStoryRequest" in result.stdout, (
        "doctrine objected, but did not say which class:\n" + result.stdout
    )


def test_a_class_that_is_neither_request_nor_response_is_objected_to(
    tmp_path: Path,
) -> None:
    """Read by no rule at all while a suffix was what made it visible."""
    root = tmp_path / "other-name"
    context = a_solution(root)
    (context / "dtos" / "story.py").write_text(
        A_PLAIN_CLASS.format(name="StoryMessage")
    )

    result = run_doctrine(root, MESSAGES_TEST, DTOS_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, DTOS_SELECTOR)
    assert objects(result), (
        "doctrine passed over a class in dtos/ that is not a pydantic "
        "model:\n" + result.stdout
    )
    assert "stories.StoryMessage" in result.stdout, (
        "doctrine objected, but did not say which class:\n" + result.stdout
    )


def test_an_enum_and_a_message_built_on_another_are_not_objected_to(
    tmp_path: Path,
) -> None:
    """An enum typing a field belongs with the message that uses it, and
    a model extending a model is a model."""
    root = tmp_path / "nested"
    context = a_solution(root)
    (context / "dtos" / "story.py").write_text(A_NESTED_MESSAGE)

    result = run_doctrine(root, MESSAGES_TEST, DTOS_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, DTOS_SELECTOR)
    assert not objects(result), (
        "doctrine objected to an enum or a derived message in dtos/:\n" + result.stdout
    )


def test_a_pydantic_dataclass_is_objected_to(tmp_path: Path) -> None:
    """As it is for a request or a response: it belongs to neither ring."""
    root = tmp_path / "pydantic-dataclass"
    context = a_solution(root)
    (context / "dtos" / "story.py").write_text(A_PYDANTIC_DATACLASS)

    result = run_doctrine(root, MESSAGES_TEST, DTOS_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, DTOS_SELECTOR)
    assert objects(result), (
        "doctrine passed over a pydantic dataclass in dtos/:\n" + result.stdout
    )
    assert "pydantic dataclass" in result.stdout, (
        "doctrine objected, but did not say why:\n" + result.stdout
    )


def test_a_dtos_module_that_does_not_import_is_objected_to_once(
    tmp_path: Path,
) -> None:
    """The file is named, and its classes are not each named after it."""
    root = tmp_path / "does-not-import"
    context = a_solution(root)
    (context / "dtos" / "story.py").write_text(
        '"""Messages that need something not installed."""\n\n'
        "from not_installed_anywhere import Base\n\n\n"
        "class StoryMessage(Base):\n"
        '    """A story."""\n\n\n'
        "class EpicMessage(Base):\n"
        '    """An epic."""\n'
    )

    result = run_doctrine(root, MESSAGES_TEST, DTOS_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, DTOS_SELECTOR)
    assert objects(result), (
        "doctrine passed over a dtos/ module it could not import:\n" + result.stdout
    )
    assert "dtos/story.py" in result.stdout, (
        "doctrine objected, but did not name the file:\n" + result.stdout
    )
    assert "stories.StoryMessage" not in result.stdout, (
        "doctrine named a class it could not import as well as its "
        "file:\n" + result.stdout
    )
