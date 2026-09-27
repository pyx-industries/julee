"""The DTO doctrine, run against solutions written for the purpose.

Every other test here checks a rule function. These check the suite:
doctrine is pointed at a solution on disk and the outcome is asserted,
so severing the wire between a rule and its assertion, or deleting the
doctrine test, fails the build.

Both were done deliberately before this file existed. Neither was
caught: the rule kept all its unit tests, and the suite simply ran one
test fewer.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[5]
"""The repository root, which the doctrine run needs as its cwd.

Counted from this file: doctrine_suite, tests, core, julee, src, root.
Written as parents[4] first, which is src/, where pytest finds no
config and collects nothing — and a run that collects nothing has no
failures, so every "must fail" test passed for the wrong reason.
"""
DOCTRINE_TEST = "src/julee/core/doctrine/test_use_case.py"
SELECTOR = "pydantic_DTO"
EXPECTED_TESTS = 2
"""How many tests the selector must collect.

Asserted rather than assumed. A deleted doctrine test collects nothing,
pytest exits 5, and without this the suite would read as "no failures".
"""

GOOD = '''"""Get a story."""

from pydantic import BaseModel


class GetStoryRequest(BaseModel):
    """Which story."""

    slug: str


class GetStoryResponse(BaseModel):
    """The story."""

    title: str


class GetStoryUseCase:
    """Fetch one story by its slug."""

    async def execute(self, request: GetStoryRequest) -> GetStoryResponse:
        """Fetch it."""
        return GetStoryResponse(title="x")
'''

PLAIN_REQUEST = GOOD.replace(
    "class GetStoryRequest(BaseModel):", "class GetStoryRequest:"
)

PLAIN_RESPONSE = GOOD.replace(
    "class GetStoryResponse(BaseModel):", "class GetStoryResponse:"
)

PYDANTIC_DATACLASS_REQUEST = GOOD.replace(
    "from pydantic import BaseModel",
    "from pydantic import BaseModel\nfrom pydantic.dataclasses import dataclass",
).replace(
    "class GetStoryRequest(BaseModel):",
    "@dataclass(frozen=True)\nclass GetStoryRequest:",
)

STDLIB_DATACLASS_REQUEST = GOOD.replace(
    "from pydantic import BaseModel",
    "from dataclasses import dataclass\n\nfrom pydantic import BaseModel",
).replace(
    "class GetStoryRequest(BaseModel):",
    "@dataclass(frozen=True)\nclass GetStoryRequest:",
)

REQUEST_FROM_ELSEWHERE = '''"""Get a story."""

from acme.stories.messages import GetStoryRequest, GetStoryResponse

__all__ = ["GetStoryRequest", "GetStoryResponse"]


class GetStoryUseCase:
    """Fetch one story by its slug."""

    async def execute(self, request: GetStoryRequest) -> GetStoryResponse:
        """Fetch it."""
        return GetStoryResponse()
'''

MESSAGES_ELSEWHERE = '''"""Messages, kept out of usecases/."""


class GetStoryRequest:
    """Not pydantic."""


class GetStoryResponse:
    """Not pydantic either."""
'''

LOCAL_BASEMODEL = '''"""Get a story."""


class BaseModel:
    """Ours, not pydantic's."""


class GetStoryRequest(BaseModel):
    """Which story."""


class GetStoryResponse(BaseModel):
    """The story."""


class GetStoryUseCase:
    """Fetch one story by its slug."""

    async def execute(self, request: GetStoryRequest) -> GetStoryResponse:
        """Fetch it."""
        return GetStoryResponse()
'''


def a_solution(tmp_path: Path, usecase: str, messages: str = "") -> Path:
    """Write a julee solution with one bounded context.

    Args:
        tmp_path: Where to write it
        usecase: Source for usecases/get_story.py
        messages: Source for a messages.py outside usecases/, if any

    Returns:
        The solution root, ready to pass as JULEE_TARGET
    """
    root = tmp_path / "solution"
    context = root / "src" / "acme" / "stories"
    (context / "usecases").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "acme"\nversion = "0.1.0"\n\n'
        '[tool.julee]\nsearch_root = "src/acme"\ndocs_root = "docs"\n'
    )
    (root / "src" / "acme" / "__init__.py").write_text('"""Acme."""\n')
    (context / "__init__.py").write_text('"""Stories."""\n')
    (context / "usecases" / "__init__.py").write_text("")
    (context / "usecases" / "get_story.py").write_text(usecase)
    if messages:
        (context / "messages.py").write_text(messages)
    return root


def run_doctrine(target: Path) -> subprocess.CompletedProcess[str]:
    """Run the DTO doctrine against a solution, as a real pytest run.

    A subprocess rather than an in-process call, because what is under
    test is the doctrine suite: its collection, its fixtures and its
    assertions, not a function it happens to call.

    Args:
        target: The solution root

    Returns:
        The finished process, stdout captured
    """
    env = {
        **os.environ,
        "JULEE_TARGET": str(target),
        "PYTHONPATH": str(target / "src"),
    }
    env.pop("COV_CORE_SOURCE", None)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            DOCTRINE_TEST,
            "-k",
            SELECTOR,
            "-q",
            "--no-cov",
            "-p",
            "no:cacheprovider",
            "-p",
            "no:xdist",
            "-o",
            "addopts=",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


def assert_ran_both(result: subprocess.CompletedProcess[str]) -> None:
    """The selector must still collect both tests.

    Without this a deleted doctrine test reads as a clean run.
    """
    assert "no tests ran" not in result.stdout, (
        f"the doctrine tests were not collected — has {SELECTOR} been "
        f"renamed or deleted?\n{result.stdout}"
    )
    ran = sum(
        int(count) for count, _ in re.findall(r"(\d+) (passed|failed)", result.stdout)
    )
    assert ran == EXPECTED_TESTS, (
        f"expected {EXPECTED_TESTS} doctrine tests, {ran} ran — one has "
        f"been deleted or renamed:\n{result.stdout}"
    )


def test_a_solution_whose_dtos_are_pydantic_passes(tmp_path: Path) -> None:
    """The suite must not fail correct code.

    A rule that fires on everything guarantees as little as one that
    fires on nothing.
    """
    result = run_doctrine(a_solution(tmp_path, GOOD))

    assert_ran_both(result)
    assert result.returncode == 0, result.stdout
    assert f"{EXPECTED_TESTS} passed" in result.stdout, result.stdout


@pytest.mark.parametrize(
    ("what", "usecase", "messages"),
    [
        ("a request inheriting nothing", PLAIN_REQUEST, ""),
        ("a response inheriting nothing", PLAIN_RESPONSE, ""),
        ("a pydantic dataclass request", PYDANTIC_DATACLASS_REQUEST, ""),
        ("a stdlib dataclass request", STDLIB_DATACLASS_REQUEST, ""),
        ("a local class called BaseModel", LOCAL_BASEMODEL, ""),
        ("dtos defined outside usecases/", REQUEST_FROM_ELSEWHERE, MESSAGES_ELSEWHERE),
    ],
    ids=[
        "request-inherits-nothing",
        "response-inherits-nothing",
        "pydantic-dataclass-request",
        "stdlib-dataclass-request",
        "local-class-called-BaseModel",
        "dtos-outside-usecases",
    ],
)
def test_the_doctrine_suite_fails_on(
    tmp_path: Path, what: str, usecase: str, messages: str
) -> None:
    """Each of these must fail the doctrine suite, not merely a rule.

    Args:
        tmp_path: Where the solution is written
        what: What is wrong with it, for the failure message
        usecase: Source for its use case module
        messages: Source for a module outside usecases/, if any
    """
    result = run_doctrine(a_solution(tmp_path, usecase, messages))

    assert_ran_both(result)
    assert result.returncode != 0, (
        f"doctrine passed a solution with {what}:\n{result.stdout}"
    )
    assert "is a pydantic DTO, but" in result.stdout, (
        f"doctrine failed for some other reason than {what}:\n{result.stdout}"
    )
