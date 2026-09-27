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
        tmp_path: The solution root to write into
        usecase: Source for usecases/get_story.py
        messages: Source for a messages.py outside usecases/, if any

    Returns:
        The solution root, ready to pass as JULEE_TARGET
    """
    root = tmp_path
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


def assert_doctrine_ran(result: subprocess.CompletedProcess[str]) -> None:
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


NOT_A_BASEMODEL = {
    "a plain class": (PLAIN_REQUEST, ""),
    "a stdlib dataclass": (STDLIB_DATACLASS_REQUEST, ""),
    "a pydantic dataclass": (PYDANTIC_DATACLASS_REQUEST, ""),
    "a local class called BaseModel": (LOCAL_BASEMODEL, ""),
    "a class defined outside usecases/": (REQUEST_FROM_ELSEWHERE, MESSAGES_ELSEWHERE),
    "a response that is a plain class": (PLAIN_RESPONSE, ""),
}
"""Ways a DTO can fail to be a BaseModel.

Listed rather than left to the obvious one because every one of these
reads as compliant to a check that follows bases in the AST, which is
what the first version of this rule did.
"""


def test_dto_must_be_a_subclass_of_pydantic_baseclass(tmp_path: Path) -> None:
    """The doctrine suite passes a BaseModel DTO and fails anything else.

    Both halves in one test because they are one statement. A rule that
    fires on everything guarantees as little as one that fires on
    nothing, so the first assertion is not decoration.

    Every disguise is tried before reporting, so a failure names all of
    them that leaked rather than only the first.
    """
    good = run_doctrine(a_solution(tmp_path / "good", GOOD))
    assert_doctrine_ran(good)
    assert good.returncode == 0, f"doctrine failed correct code:\n{good.stdout}"
    assert f"{EXPECTED_TESTS} passed" in good.stdout, good.stdout

    leaked = []
    for what, (usecase, messages) in NOT_A_BASEMODEL.items():
        result = run_doctrine(
            a_solution(tmp_path / what.replace(" ", "-"), usecase, messages)
        )
        assert_doctrine_ran(result)
        if result.returncode == 0:
            leaked.append(what)
        elif "is a pydantic DTO, but" not in result.stdout:
            leaked.append(f"{what} (failed for another reason)")

    assert not leaked, "the doctrine suite accepted a DTO that is not a BaseModel: " + (
        ", ".join(leaked)
    )
