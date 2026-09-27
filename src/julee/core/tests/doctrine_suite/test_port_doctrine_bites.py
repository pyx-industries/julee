"""The driven port doctrine, run against solutions written for the purpose.

The tests in doctrine_rules/ check rule functions. This one runs the
doctrine suite itself as a subprocess against a solution on disk and
asserts the outcome, so it fails if the suite stops objecting.
"""

import re
import subprocess
from pathlib import Path

import pytest

from .harness import a_julee_solution, assert_doctrine_ran, run_doctrine

pytestmark = pytest.mark.unit

PORT_TEST = "src/julee/core/doctrine/test_driven_port.py"
PORT_SELECTOR = "only_domain_types"
EXPECTED_PORT_TESTS = 1

PORT_LAYERS = {
    "repositories": "StoryRepository",
    "services": "StoryService",
    "oracles": "StoryOracle",
    "calculators": "StoryCalculator",
    "witnesses": "StoryWitness",
    "handlers": "StoryHandler",
}
"""Every driven port directory, with a protocol name for it.

A dimension rather than one directory checked and five assumed.
"""

ENTITY = '''"""The Story entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    """A unit of work."""

    slug: str
'''

PREAMBLE = '''"""A driven port."""

from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel
from pydantic.dataclasses import dataclass as pydantic_dataclass

from acme.stories.domain.models.story import Story

Row = dict[str, Any]


class NotADataclass:
    """A plain class."""


class AModel(BaseModel):
    """A pydantic model."""


@pydantic_dataclass(frozen=True)
class APydanticDataclass:
    """A pydantic dataclass."""

    slug: str


@dataclass
class AMutableDataclass:
    """A dataclass that is not frozen."""

    slug: str
'''

SIGNATURES = {
    "a frozen dataclass": "async def get(self, slug: str) -> Story | None: ...",
    "primitives": "async def count(self, since: int) -> int: ...",
    "a tuple of dataclasses": "async def all(self) -> tuple[Story, ...]: ...",
}
"""Signatures a driven port may have."""

FORBIDDEN_SIGNATURES = {
    "Any in a return": "async def get(self, slug: str) -> Any: ...",
    "Any in a parameter": "async def put(self, value: Any) -> None: ...",
    "dict[str, Any]": "async def get(self, slug: str) -> dict[str, Any]: ...",
    "an aliased dict[str, Any]": "async def get(self, slug: str) -> Row: ...",
    "a pydantic model": "async def get(self, slug: str) -> AModel: ...",
    "a pydantic dataclass": "async def get(self, slug: str) -> APydanticDataclass: ...",
    "a mutable dataclass": "async def get(self, slug: str) -> AMutableDataclass: ...",
    "a plain class": "async def get(self, slug: str) -> NotADataclass: ...",
    "an unannotated parameter": "async def put(self, value) -> None: ...",
    "an undeclared return": "async def put(self, slug: str): ...",
}
"""Ways a driven port can speak something other than the domain.

Each is a signature that reads as ordinary Python and says nothing a
caller in the domain could act on.
"""


def a_port_module(protocol: str, signature: str) -> str:
    """A protocol module with one method of the given signature."""
    return (
        f"{PREAMBLE}\n\nclass {protocol}(Protocol):\n"
        f'    """A driven port."""\n\n    {signature}\n'
    )


def a_solution(root: Path, layer: str, protocol: str, signature: str) -> Path:
    """Write a julee solution whose one driven port has that signature.

    Args:
        root: The solution root to write into
        layer: The port directory, e.g. "repositories"
        protocol: The protocol class name
        signature: The one method it declares

    Returns:
        The root, ready to pass as JULEE_TARGET
    """
    context = a_julee_solution(root)
    (context / "domain" / "models").mkdir(parents=True)
    (context / "domain" / layer).mkdir(parents=True)
    (context / "usecases").mkdir(parents=True)
    (context / "usecases" / "__init__.py").write_text("")
    for package in (context / "domain", context / "domain" / "models"):
        (package / "__init__.py").write_text("")
    (context / "domain" / layer / "__init__.py").write_text("")
    (context / "domain" / "models" / "story.py").write_text(ENTITY)
    (context / "domain" / layer / "story.py").write_text(
        a_port_module(protocol, signature)
    )
    return root


def run_port_doctrine(target: Path) -> subprocess.CompletedProcess[str]:
    """Run the driven port type doctrine against a solution."""
    return run_doctrine(target, PORT_TEST, PORT_SELECTOR)


def test_driven_port_must_only_use_primitives_or_frozen_dataclasses(
    tmp_path: Path,
) -> None:
    """The doctrine passes a port speaking the domain and fails any other.

    Every port directory gets every signature, and every case runs
    before reporting so a failure names all of them.
    """
    wrong = []
    for layer, protocol in PORT_LAYERS.items():
        for what, signature in SIGNATURES.items():
            root = tmp_path / f"ok-{layer}-{re.sub(r'[^a-zA-Z]+', '-', what)}"
            result = run_port_doctrine(a_solution(root, layer, protocol, signature))
            assert_doctrine_ran(result, EXPECTED_PORT_TESTS, PORT_SELECTOR)
            if result.returncode != 0:
                wrong.append(f"a {layer} port using {what}")

    assert not wrong, "doctrine refused a port speaking the domain: " + ", ".join(wrong)

    leaked = []
    for layer, protocol in PORT_LAYERS.items():
        for what, signature in FORBIDDEN_SIGNATURES.items():
            root = tmp_path / f"bad-{layer}-{re.sub(r'[^a-zA-Z]+', '-', what)}"
            result = run_port_doctrine(a_solution(root, layer, protocol, signature))
            assert_doctrine_ran(result, EXPECTED_PORT_TESTS, PORT_SELECTOR)
            if result.returncode == 0:
                leaked.append(f"a {layer} port using {what}")

    assert not leaked, (
        "the doctrine suite accepted a driven port that does not speak the "
        "domain: " + ", ".join(leaked)
    )
