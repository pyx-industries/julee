"""The entity doctrine, run against solutions written for the purpose.

The tests in doctrine_rules/ check rule functions. This one runs the
doctrine suite itself as a subprocess and asserts the outcome, so it
fails if the suite stops objecting.
"""

import subprocess
from pathlib import Path

import pytest

from .harness import a_julee_solution, assert_doctrine_ran, run_doctrine

pytestmark = pytest.mark.unit

ENTITY_TEST = "src/julee/core/doctrine/test_entity.py"
ENTITY_SELECTOR = "MUST_be_frozen_dataclasses"
EXPECTED_ENTITY_TESTS = 1

PREAMBLE = '''"""The domain."""

from dataclasses import dataclass
from enum import IntEnum, StrEnum

from pydantic import BaseModel
from pydantic.dataclasses import dataclass as pydantic_dataclass

from julee.core.entities.entity import Entity


class _Authored(BaseModel):
    """A base of the solution's own, which is a pydantic model."""
'''

ALLOWED = {
    "a frozen dataclass": (
        '@dataclass(frozen=True)\nclass Story:\n    """A unit of work."""\n\n'
        "    slug: str\n"
    ),
    "a StrEnum": 'class Colour(StrEnum):\n    """A domain value."""\n\n    RED = "red"\n',
    "an IntEnum": 'class Rank(IntEnum):\n    """A domain value."""\n\n    FIRST = 1\n',
    "a str value object": (
        'class Slug(str):\n    """Immutable already, being a str."""\n\n'
        "    __slots__ = ()\n"
    ),
    "a frozen dataclass extending one": (
        '@dataclass(frozen=True)\nclass Base:\n    """A base."""\n\n    slug: str\n\n\n'
        '@dataclass(frozen=True)\nclass Derived(Base):\n    """Derived."""\n\n'
        "    title: str\n"
    ),
}
"""What a domain class may be."""

FORBIDDEN = {
    "a pydantic model": (
        'class Story(BaseModel):\n    """A unit of work."""\n\n    slug: str\n',
        "Story",
    ),
    "julee's Entity": (
        'class Story(Entity):\n    """A unit of work."""\n\n    slug: str\n',
        "Story",
    ),
    "a local base that is a pydantic model": (
        'class Story(_Authored):\n    """A unit of work."""\n\n    slug: str\n',
        "Story",
    ),
    "a pydantic dataclass": (
        '@pydantic_dataclass(frozen=True)\nclass Story:\n    """A unit of work."""\n\n'
        "    slug: str\n",
        "Story",
    ),
    "a dataclass that is not frozen": (
        '@dataclass\nclass Story:\n    """A unit of work."""\n\n    slug: str\n',
        "Story",
    ),
    "a plain class": (
        'class Story:\n    """A unit of work."""\n\n    slug: str\n',
        "Story",
    ),
}
"""What a domain class may not be, with the class each objection names."""


def a_domain_module(body: str) -> str:
    """A domain models module holding one declaration."""
    return f"{PREAMBLE}\n\n{body}"


def a_solution(root: Path, models: dict[str, str]) -> Path:
    """Write a julee solution with the given domain model modules.

    Args:
        root: The solution root to write into
        models: Module stem mapped to the declaration it holds

    Returns:
        The root, ready to pass as JULEE_TARGET
    """
    context = a_julee_solution(root)
    (context / "domain" / "models").mkdir(parents=True)
    (context / "usecases").mkdir(parents=True)
    for package in (
        context / "domain",
        context / "domain" / "models",
        context / "usecases",
    ):
        (package / "__init__.py").write_text("")
    for stem, body in models.items():
        (context / "domain" / "models" / f"{stem}.py").write_text(a_domain_module(body))
    return root


def run_entity_doctrine(target: Path) -> subprocess.CompletedProcess[str]:
    """Run the entity doctrine against a solution."""
    return run_doctrine(target, ENTITY_TEST, ENTITY_SELECTOR)


def test_an_entity_must_be_a_frozen_stdlib_dataclass(tmp_path: Path) -> None:
    """The doctrine passes what the domain may be and fails everything else.

    Every case runs before reporting, so a failure names all of them.
    """
    good = run_entity_doctrine(
        a_solution(
            tmp_path / "good",
            {f"m{n}": body for n, body in enumerate(ALLOWED.values())},
        )
    )
    assert_doctrine_ran(good, EXPECTED_ENTITY_TESTS, ENTITY_SELECTOR)
    assert good.returncode == 0, f"doctrine refused a domain class:\n{good.stdout}"

    missed = []
    for what, (body, named) in FORBIDDEN.items():
        bad = run_entity_doctrine(
            a_solution(tmp_path / what.replace(" ", "-").replace("'", ""), {"m": body})
        )
        assert_doctrine_ran(bad, EXPECTED_ENTITY_TESTS, ENTITY_SELECTOR)
        if bad.returncode == 0 or f".{named}:" not in bad.stdout:
            missed.append(what)

    assert not missed, "the doctrine suite did not object to: " + ", ".join(missed)
