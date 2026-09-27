"""The DTO doctrine, run against solutions written for the purpose.

The tests in doctrine_rules/ check rule functions. This one runs the
doctrine suite itself as a subprocess against a solution on disk and
asserts the outcome, so it fails if the suite stops objecting.
"""

import re
from collections.abc import Callable
from pathlib import Path

import pytest

from .harness import a_julee_solution, assert_doctrine_ran, run_doctrine

pytestmark = pytest.mark.unit

DOCTRINE_TEST = "src/julee/core/doctrine/test_use_case.py"
SELECTOR = "pydantic_DTO"
EXPECTED_TESTS = 2
"""How many tests the selector must collect.

A deleted doctrine test collects nothing, and a run that collects
nothing reports no failures.
"""

ROLES = ("request", "response")


def class_of(role: str) -> str:
    """The class name a role has, e.g. GetStoryRequest."""
    return f"GetStory{role.capitalize()}"


def other_than(role: str) -> str:
    """The other role."""
    return "response" if role == "request" else "request"


def a_basemodel(name: str) -> str:
    """A DTO deriving from pydantic.BaseModel."""
    return f'class {name}(BaseModel):\n    """A message."""\n'


def a_plain_class(name: str) -> str:
    """A DTO deriving from nothing."""
    return f'class {name}:\n    """A message."""\n'


def a_stdlib_dataclass(name: str) -> str:
    """A DTO built with dataclasses.dataclass."""
    return f'@dataclass(frozen=True)\nclass {name}:\n    """A message."""\n'


def a_pydantic_dataclass(name: str) -> str:
    """A DTO built with pydantic.dataclasses.dataclass."""
    return f'@pydantic_dataclass(frozen=True)\nclass {name}:\n    """A message."""\n'


def a_local_basemodel(name: str) -> str:
    """A DTO deriving from a local class named BaseModel."""
    return f'class {name}(_BaseModel):\n    """A message."""\n'


SHAPES: dict[str, Callable[[str], str]] = {
    "a plain class": a_plain_class,
    "a stdlib dataclass": a_stdlib_dataclass,
    "a pydantic dataclass": a_pydantic_dataclass,
    "a local class called BaseModel": a_local_basemodel,
}
"""What a DTO can be instead of a BaseModel."""

PREAMBLE = '''"""Get a story."""

from dataclasses import dataclass

from pydantic import BaseModel
from pydantic.dataclasses import dataclass as pydantic_dataclass


class _BaseModel:
    """A class named BaseModel that is not pydantic\'s."""
'''

USE_CASE = '''

class GetStoryUseCase:
    """Fetch one story by its slug."""

    async def execute(self, request: GetStoryRequest) -> GetStoryResponse:
        """Fetch it."""
        raise NotImplementedError
'''


def a_usecase_module(request: str, response: str, imported: str = "") -> str:
    """Assemble a use case module from its two DTOs.

    Args:
        request: Source for the request class, or "" if imported
        response: Source for the response class, or "" if imported
        imported: An import line, for a DTO defined elsewhere

    Returns:
        The module source
    """
    parts = [PREAMBLE]
    if imported:
        parts.append(f"\n{imported}\n")
    parts.extend(f"\n\n{source}" for source in (request, response) if source)
    parts.append(USE_CASE)
    return "".join(parts)


def a_solution(root: Path, usecase: str, messages: str = "") -> Path:
    """Write a julee solution with one bounded context.

    Args:
        root: The solution root to write into
        usecase: Source for usecases/get_story.py
        messages: Source for a messages.py outside usecases/, if any

    Returns:
        The root, ready to pass as JULEE_TARGET
    """
    context = a_julee_solution(root)
    (context / "usecases").mkdir(parents=True)
    (context / "usecases" / "__init__.py").write_text("")
    (context / "usecases" / "get_story.py").write_text(usecase)
    if messages:
        (context / "messages.py").write_text(messages)
    return root


def not_a_basemodel() -> dict[str, tuple[str, str]]:
    """Every shape in SHAPES, applied to each role in turn.

    The other role is left as a BaseModel, so a failure names the half
    that was broken.

    Returns:
        What is wrong, mapped to the use case and messages sources
    """
    cases: dict[str, tuple[str, str]] = {}

    for role in ROLES:
        name = class_of(role)
        counterpart = a_basemodel(class_of(other_than(role)))

        for shape, build in SHAPES.items():
            broken = build(name)
            request, response = (
                (broken, counterpart) if role == "request" else (counterpart, broken)
            )
            cases[f"a {role} that is {shape}"] = (
                a_usecase_module(request, response),
                "",
            )

        request, response = (
            ("", counterpart) if role == "request" else (counterpart, "")
        )
        cases[f"a {role} defined outside usecases/"] = (
            a_usecase_module(
                request,
                response,
                imported=f"from acme.stories.messages import {name}",
            ),
            f'"""Messages."""\n\n\nclass {name}:\n    """Not pydantic."""\n',
        )

    return cases


NOT_A_BASEMODEL = not_a_basemodel()

GOOD = a_usecase_module(a_basemodel("GetStoryRequest"), a_basemodel("GetStoryResponse"))


def test_dto_must_be_a_subclass_of_pydantic_baseclass(tmp_path: Path) -> None:
    """The doctrine suite passes a BaseModel DTO and fails anything else.

    Both directions are asserted, and every case runs before reporting
    so a failure names all of them.
    """
    good = run_doctrine(a_solution(tmp_path / "good", GOOD), DOCTRINE_TEST, SELECTOR)
    assert_doctrine_ran(good, EXPECTED_TESTS, SELECTOR)
    assert good.returncode == 0, f"doctrine failed correct code:\n{good.stdout}"
    assert f"{EXPECTED_TESTS} passed" in good.stdout, good.stdout

    leaked = []
    for what, (usecase, messages) in NOT_A_BASEMODEL.items():
        root = tmp_path / re.sub(r"[^a-zA-Z]+", "-", what)
        result = run_doctrine(
            a_solution(root, usecase, messages), DOCTRINE_TEST, SELECTOR
        )
        assert_doctrine_ran(result, EXPECTED_TESTS, SELECTOR)
        if result.returncode == 0:
            leaked.append(what)
        elif "is a pydantic DTO, but" not in result.stdout:
            leaked.append(f"{what} (failed for another reason)")

    assert not leaked, "the doctrine suite accepted a DTO that is not a BaseModel: " + (
        ", ".join(leaked)
    )
