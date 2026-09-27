"""The driven port doctrine, run against solutions written for the purpose.

The tests in doctrine_rules/ check rule functions. This one runs the
doctrine suite itself as a subprocess against a solution on disk and
asserts the outcome, so it fails if the suite stops objecting.
"""

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

EXTRAS = '''"""Types a port should not be speaking."""

from dataclasses import dataclass

from pydantic import BaseModel
from pydantic.dataclasses import dataclass as pydantic_dataclass


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
"""Kept out of the port directory, where every class is read as a port."""

PREAMBLE = '''"""A driven port."""

from typing import Any, Protocol

from acme.stories.domain.models.extras import (
    AModel,
    AMutableDataclass,
    APydanticDataclass,
    NotADataclass,
)
from acme.stories.domain.models.story import Story

Row = dict[str, Any]
'''

ALLOWED = (
    "async def get(self, slug: str) -> Story | None: ...",
    "async def count(self, since: int) -> int: ...",
    "async def all(self) -> tuple[Story, ...]: ...",
    "async def touch(self) -> None: ...",
)
"""Signatures a driven port may have."""

FORBIDDEN = {
    "any_return": "async def any_return(self, slug: str) -> Any: ...",
    "any_parameter": "async def any_parameter(self, value: Any) -> None: ...",
    "dict_of_any": "async def dict_of_any(self) -> dict[str, Any]: ...",
    "aliased_dict_of_any": "async def aliased_dict_of_any(self) -> Row: ...",
    "a_pydantic_model": "async def a_pydantic_model(self) -> AModel: ...",
    "a_pydantic_dataclass": (
        "async def a_pydantic_dataclass(self) -> APydanticDataclass: ..."
    ),
    "a_mutable_dataclass": (
        "async def a_mutable_dataclass(self) -> AMutableDataclass: ..."
    ),
    "a_plain_class": "async def a_plain_class(self) -> NotADataclass: ...",
    "unannotated_parameter": "async def unannotated_parameter(self, value) -> None: ...",
    "undeclared_return": "async def undeclared_return(self, slug: str): ...",
}
"""Ways a driven port can speak something other than the domain.

Keyed by method name, so one protocol carries them all and the
objections can be told apart in one run.
"""


def a_port_module(protocol: str, signatures: tuple[str, ...]) -> str:
    """A protocol module declaring the given methods."""
    body = "\n\n".join(f"    {signature}" for signature in signatures)
    return (
        f"{PREAMBLE}\n\nclass {protocol}(Protocol):\n"
        f'    """A driven port."""\n\n' + body + "\n"
    )


def a_solution(
    root: Path, layer: str, protocol: str, signatures: tuple[str, ...]
) -> Path:
    """Write a julee solution whose one driven port declares those methods.

    Args:
        root: The solution root to write into
        layer: The port directory, e.g. "repositories"
        protocol: The protocol class name
        signatures: The methods it declares

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
    (context / "domain" / "models" / "extras.py").write_text(EXTRAS)
    (context / "domain" / layer / "story.py").write_text(
        a_port_module(protocol, signatures)
    )
    return root


def run_port_doctrine(target: Path) -> subprocess.CompletedProcess[str]:
    """Run the driven port type doctrine against a solution."""
    return run_doctrine(target, PORT_TEST, PORT_SELECTOR)


def test_driven_port_must_only_use_primitives_or_frozen_dataclasses(
    tmp_path: Path,
) -> None:
    """The doctrine passes a port speaking the domain and fails any other.

    Every port directory gets both, and every case runs before
    reporting so a failure names all of them.
    """
    refused = []
    missed = []

    for layer, protocol in PORT_LAYERS.items():
        good = run_port_doctrine(
            a_solution(tmp_path / f"ok-{layer}", layer, protocol, ALLOWED)
        )
        assert_doctrine_ran(good, EXPECTED_PORT_TESTS, PORT_SELECTOR)
        if good.returncode != 0:
            refused.append(f"a {layer} port speaking the domain:\n{good.stdout}")

        bad = run_port_doctrine(
            a_solution(
                tmp_path / f"bad-{layer}",
                layer,
                protocol,
                tuple(FORBIDDEN.values()),
            )
        )
        assert_doctrine_ran(bad, EXPECTED_PORT_TESTS, PORT_SELECTOR)
        if bad.returncode == 0:
            missed.append(f"every offence in a {layer} port")
            continue
        missed.extend(
            f"{method} in a {layer} port"
            for method in FORBIDDEN
            if method not in bad.stdout
        )

    assert not refused, "doctrine refused a port speaking the domain: " + "".join(
        refused
    )
    assert not missed, "the doctrine suite did not object to: " + ", ".join(missed)
