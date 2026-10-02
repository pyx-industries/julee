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
from typing import Any, NewType
from uuid import UUID

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


class Ref(str):
    """A value object built on str, the shape Slug and Name have."""

    __slots__ = ()


class Score(int):
    """A value object built on int."""

    __slots__ = ()


StoryId = NewType("StoryId", UUID)
"""An identifier: a UUID to Python, a type of its own to a type checker."""

DraftId = NewType("DraftId", StoryId)
"""A NewType over a NewType."""

WrappedModel = NewType("WrappedModel", AModel)
"""A NewType over something a port may not name."""

WrappedAny = NewType("WrappedAny", Any)  # type: ignore[valid-newtype]
"""A NewType over Any, which Python allows and a type checker does not."""
'''
"""Kept out of the port directory, where every class is read as a port."""

PREAMBLE = '''"""A driven port."""

from typing import Any, Protocol

from acme.stories.domain.models.extras import (
    AModel,
    AMutableDataclass,
    APydanticDataclass,
    DraftId,
    NotADataclass,
    Ref,
    Score,
    StoryId,
    WrappedAny,
    WrappedModel,
)
from acme.stories.domain.models.story import Story

Row = dict[str, Any]
'''

ALLOWED = (
    "async def get(self, slug: str) -> Story | None: ...",
    "async def count(self, since: int) -> int: ...",
    "async def all(self) -> tuple[Story, ...]: ...",
    "async def touch(self) -> None: ...",
    # A value object built on str or int. The domain ring sanctions
    # these (VALUE_OBJECT_BASES) and a port naming one is stronger than
    # a port naming str: it is the difference between a multihash and
    # any old text (julee#44).
    "async def named(self, ref: Ref) -> Ref: ...",
    "async def scored(self) -> Score: ...",
    # A NewType is judged by what it wraps. An identifier declared as
    # NewType("StoryId", UUID) is a UUID, which a port may name, and
    # says which UUID it is.
    "async def by_id(self, story_id: StoryId) -> Story | None: ...",
    "async def ids(self) -> tuple[StoryId, ...]: ...",
    "async def draft(self, draft_id: DraftId) -> None: ...",
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
    "a_newtype_over_a_model": (
        "async def a_newtype_over_a_model(self) -> WrappedModel: ..."
    ),
    "a_newtype_over_any": "async def a_newtype_over_any(self) -> WrappedAny: ...",
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


GENERIC_BASE = '''"""A generic base protocol, and two ports built on it."""

from typing import Protocol, TypeVar, runtime_checkable

from acme.stories.domain.models.extras import AModel
from acme.stories.domain.models.story import Story

T = TypeVar("T")


@runtime_checkable
class Keeps(Protocol[T]):
    """What every repository in this context can do.

    Generic in its entity, so it is a base rather than a port: T is
    decided by whoever inherits it.
    """

    async def get(self, entity_id: str) -> T | None: ...

    async def save(self, entity: T) -> None: ...


@runtime_checkable
class StoryRepository(Keeps[Story], Protocol):
    """A port. Keeps' T is a Story here."""


@runtime_checkable
class ModelRepository(Keeps[AModel], Protocol):
    """A port that binds T to something it may not."""
'''


def a_solution_with_a_generic_base(root: Path) -> Path:
    """Write a solution whose repositories share a generic base.

    Args:
        root: The solution root to write into

    Returns:
        The root, ready to pass as JULEE_TARGET
    """
    context = a_julee_solution(root)
    (context / "domain" / "models").mkdir(parents=True)
    (context / "domain" / "repositories").mkdir(parents=True)
    (context / "usecases").mkdir(parents=True)
    (context / "usecases" / "__init__.py").write_text("")
    for package in (
        context / "domain",
        context / "domain" / "models",
        context / "domain" / "repositories",
    ):
        (package / "__init__.py").write_text("")
    (context / "domain" / "models" / "story.py").write_text(ENTITY)
    (context / "domain" / "models" / "extras.py").write_text(EXTRAS)
    (context / "domain" / "repositories" / "keeps.py").write_text(GENERIC_BASE)
    return root


def test_a_generic_base_is_judged_where_it_is_bound(tmp_path: Path) -> None:
    """A protocol still generic in its entity is a base, not a port.

    hcd declares HcdRepository[T] and builds seven repositories on it.
    Read on its own it returns a bare T, which says nothing about what
    crosses any port: T is whatever the subclass decided. Objecting
    there reports the base class rather than the port in front of it,
    and the only way to quiet it would be to bind T to pydantic — the
    opposite of what the rule exists to require.

    So the base is skipped and the bindings are judged. This asserts
    both halves: skipping must not take the offending binding with it.
    """
    result = run_port_doctrine(a_solution_with_a_generic_base(tmp_path / "generic"))

    assert_doctrine_ran(result, EXPECTED_PORT_TESTS, PORT_SELECTOR)
    assert "unbounded type variable" not in result.stdout, (
        "doctrine objected to a generic base protocol:\n" + result.stdout
    )
    assert "ModelRepository" in result.stdout, (
        "doctrine stopped objecting to a port that binds its base to a "
        "pydantic model:\n" + result.stdout
    )
    assert "StoryRepository" not in result.stdout, (
        "doctrine objected to a port bound to a frozen dataclass:\n" + result.stdout
    )
