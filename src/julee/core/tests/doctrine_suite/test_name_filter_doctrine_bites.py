"""What doctrine does with a class a name used to hide, run against real solutions.

The class parser left out a class whose name begins Test and a module
whose name begins with an underscore, without saying so (ADR 021). A
class in either was held to no rule.

Each case is written twice, differing only in the name, because the name
was the whole difference between an objection and a pass.
"""

from pathlib import Path

import pytest

from .harness import a_julee_solution, assert_doctrine_ran, run_doctrine

pytestmark = pytest.mark.unit

ENTITY_TEST = "src/julee/core/doctrine/test_entity.py"
ENTITY_SELECTOR = "MUST_be_frozen_dataclasses"
USE_CASE_TEST = "src/julee/core/doctrine/test_use_case.py"
NAMING_SELECTOR = "end_with_UseCase"
EXPECTED_TESTS = 1

ENTITY = '''"""The Story entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    """A unit of work."""

    slug: str
'''

AN_ENTITY_THAT_CAN_BE_CHANGED = '''"""A result."""

from dataclasses import dataclass


@dataclass
class {name}:
    """Not frozen, which an entity must be."""

    score: int
'''

A_FROZEN_ENTITY = '''"""A result."""

from dataclasses import dataclass


@dataclass(frozen=True)
class {name}:
    """Frozen, as an entity is."""

    score: int
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

A_HELPER = '''"""Something kept beside the use cases."""


class StoryHelpers:
    """Not a use case."""
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


@pytest.mark.parametrize("name", ["ExamResult", "TestResult", "Testimonial"])
def test_an_entity_that_can_be_changed_is_objected_to_whatever_it_is_called(
    tmp_path: Path, name: str
) -> None:
    """TestResult passed until the parser stopped going by the name."""
    root = tmp_path / "mutable"
    context = a_solution(root)
    (context / "domain" / "models" / "result.py").write_text(
        AN_ENTITY_THAT_CAN_BE_CHANGED.format(name=name)
    )

    result = run_doctrine(root, ENTITY_TEST, ENTITY_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, ENTITY_SELECTOR)
    assert result.returncode != 0, (
        f"doctrine passed over a mutable entity named {name}:\n" + result.stdout
    )
    assert f"stories.{name}" in result.stdout, (
        "doctrine objected, but did not say which class:\n" + result.stdout
    )


def test_a_frozen_entity_named_like_a_test_is_not_objected_to(
    tmp_path: Path,
) -> None:
    """Being read is not being objected to. The name is not the offence."""
    root = tmp_path / "frozen"
    context = a_solution(root)
    (context / "domain" / "models" / "result.py").write_text(
        A_FROZEN_ENTITY.format(name="TestResult")
    )

    result = run_doctrine(root, ENTITY_TEST, ENTITY_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, ENTITY_SELECTOR)
    assert result.returncode == 0, (
        "doctrine objected to a frozen entity for its name:\n" + result.stdout
    )


@pytest.mark.parametrize("module", ["helpers.py", "_helpers.py", "__init__.py"])
def test_a_helper_in_usecases_is_objected_to_whatever_its_module_is_called(
    tmp_path: Path, module: str
) -> None:
    """An underscore on the file was a way round ADR 020, and so was the
    package's own __init__.py."""
    root = tmp_path / "helper"
    context = a_solution(root)
    (context / "usecases" / module).write_text(A_HELPER)

    result = run_doctrine(root, USE_CASE_TEST, NAMING_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_TESTS, NAMING_SELECTOR)
    assert result.returncode != 0, (
        f"doctrine passed over a helper in usecases/{module}:\n" + result.stdout
    )
    assert "stories.StoryHelpers" in result.stdout, (
        "doctrine objected, but did not say which class:\n" + result.stdout
    )
