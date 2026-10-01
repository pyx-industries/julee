"""What doctrine does with a class in usecases/, run against real solutions.

A class in usecases/ is a use case (ADR 020), found by where it sits. Its
name and whether it can be executed are rules. Until that, only a class
named *UseCase was read, so the naming rule ran over a list already
filtered by the suffix, and a class called anything else was objected to
by nothing.

The direction that was silent is the one tested hardest: a class that is
not a valid use case, sitting in usecases/.
"""

from pathlib import Path

import pytest

from .harness import a_julee_solution, assert_doctrine_ran, run_doctrine

pytestmark = pytest.mark.unit

USE_CASE_TEST = "src/julee/core/doctrine/test_use_case.py"
NAMING_SELECTOR = "end_with_UseCase"
EXECUTE_SELECTOR = "have_execute_method"
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


class {name}:
    """Plans a story."""

    async def execute(self, request: PlanStoryRequest) -> PlanStoryResponse:
        return PlanStoryResponse(slug=request.slug)
'''

A_HELPER = '''"""Something a use case module grew beside it."""


class StoryHelpers:
    """Not a use case, and in usecases/ all the same."""

    def tidy(self, slug: str) -> str:
        return slug.strip()
'''

A_BASE_NAMED_LIKE_ONE = '''"""Wiring shared by use cases."""


class BaseStoryUseCase:
    """Holds a repository and can do nothing with it."""

    def __init__(self, repository: object) -> None:
        self.repository = repository
'''


def a_solution(root: Path, use_case_name: str = "PlanStoryUseCase") -> Path:
    """Write a solution with one use case and its messages.

    Args:
        root: The solution root to write into
        use_case_name: What the one use case is called

    Returns:
        The bounded context directory, for the caller to add to
    """
    context = a_julee_solution(root)
    for package in ("domain", "domain/models", "dtos", "usecases"):
        (context / package).mkdir(parents=True)
        (context / package / "__init__.py").write_text("")
    (context / "domain" / "models" / "story.py").write_text(ENTITY)
    (context / "dtos" / "plan_story.py").write_text(DTOS)
    (context / "usecases" / "plan_story.py").write_text(
        A_USE_CASE.format(name=use_case_name)
    )
    return context


def test_a_use_case_named_like_one_is_not_objected_to(tmp_path: Path) -> None:
    root = tmp_path / "named"
    a_solution(root)

    result = run_doctrine(root, USE_CASE_TEST, NAMING_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, NAMING_SELECTOR)
    assert result.returncode == 0, (
        "doctrine objected to a use case named *UseCase:\n" + result.stdout
    )


def test_a_use_case_not_named_like_one_is_objected_to(tmp_path: Path) -> None:
    """It executes, takes a request and returns a response, and is called
    PlanStory. Nothing read it while the suffix was how it was found."""
    root = tmp_path / "misnamed"
    a_solution(root, use_case_name="PlanStory")
    # Something must still be named *UseCase, or the canary for a broken
    # detector would fail the test instead of the rule.
    (root / "src/acme/stories/usecases/archive_story.py").write_text(
        A_USE_CASE.format(name="ArchiveStoryUseCase")
    )

    result = run_doctrine(root, USE_CASE_TEST, NAMING_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, NAMING_SELECTOR)
    assert result.returncode != 0, (
        "doctrine passed over a use case not named *UseCase:\n" + result.stdout
    )
    assert "stories.PlanStory" in result.stdout, (
        "doctrine objected, but did not say which class:\n" + result.stdout
    )


def test_a_helper_in_usecases_is_objected_to_for_its_name(tmp_path: Path) -> None:
    """Nothing but use cases and their messages lives in usecases/."""
    root = tmp_path / "helper-name"
    context = a_solution(root)
    (context / "usecases" / "helpers.py").write_text(A_HELPER)

    result = run_doctrine(root, USE_CASE_TEST, NAMING_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, NAMING_SELECTOR)
    assert result.returncode != 0, (
        "doctrine passed over a class in usecases/ that is not a use "
        "case:\n" + result.stdout
    )
    assert "stories.StoryHelpers" in result.stdout, (
        "doctrine objected, but did not say which class:\n" + result.stdout
    )


def test_a_helper_in_usecases_is_objected_to_for_having_no_execute(
    tmp_path: Path,
) -> None:
    root = tmp_path / "helper-execute"
    context = a_solution(root)
    (context / "usecases" / "helpers.py").write_text(A_HELPER)

    result = run_doctrine(root, USE_CASE_TEST, EXECUTE_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, EXECUTE_SELECTOR)
    assert result.returncode != 0, (
        "doctrine passed over a class in usecases/ that cannot be "
        "executed:\n" + result.stdout
    )
    assert "stories.StoryHelpers" in result.stdout, (
        "doctrine objected, but did not say which class:\n" + result.stdout
    )


def test_a_base_named_like_a_use_case_is_objected_to_for_having_no_execute(
    tmp_path: Path,
) -> None:
    """The suffix alone never made a class a use case. It made it found."""
    root = tmp_path / "base"
    context = a_solution(root)
    (context / "usecases" / "base.py").write_text(A_BASE_NAMED_LIKE_ONE)

    result = run_doctrine(root, USE_CASE_TEST, EXECUTE_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, EXECUTE_SELECTOR)
    assert result.returncode != 0, (
        "doctrine passed over a *UseCase with no execute():\n" + result.stdout
    )
    assert "stories.BaseStoryUseCase" in result.stdout, (
        "doctrine objected, but did not say which class:\n" + result.stdout
    )


def test_a_request_declared_in_usecases_is_not_taken_for_a_use_case(
    tmp_path: Path,
) -> None:
    """A message is found by its own suffix, and is not held to these rules."""
    root = tmp_path / "message"
    context = a_solution(root)
    (context / "usecases" / "messages.py").write_text(
        '"""A message kept beside its use case."""\n\n\n'
        "class ArchiveStoryRequest:\n"
        '    """Which story to archive."""\n'
    )

    result = run_doctrine(root, USE_CASE_TEST, NAMING_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, NAMING_SELECTOR)
    assert result.returncode == 0, (
        "doctrine took a request for a use case:\n" + result.stdout
    )
