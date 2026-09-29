"""Tests for the rule about what a domain class may be."""

import itertools
import sys
from pathlib import Path

import pytest

from julee.core.doctrine.resolution import entity_verdicts
from julee.core.doctrine.rules.entity import (
    entities_not_extending_Entity,
    entities_that_are_not_frozen_dataclasses,
)
from julee.core.entities.code_info import ClassInfo

pytestmark = pytest.mark.unit

_UNIQUE = itertools.count()

PREAMBLE = """\"\"\"The domain.\"\"\"

from dataclasses import dataclass
from enum import IntEnum, StrEnum

from pydantic import BaseModel
from pydantic.dataclasses import dataclass as pydantic_dataclass

"""

ALLOWED = {
    "a frozen dataclass": (
        '@dataclass(frozen=True)\nclass Story:\n    """A story."""\n\n    slug: str\n'
    ),
    "a StrEnum": 'class Story(StrEnum):\n    """A value."""\n\n    RED = "red"\n',
    "an IntEnum": 'class Story(IntEnum):\n    """A value."""\n\n    FIRST = 1\n',
    "a str value object": 'class Story(str):\n    """A value."""\n\n    __slots__ = ()\n',
    "an int value object": 'class Story(int):\n    """A value."""\n',
    "a frozen dataclass extending one": (
        '@dataclass(frozen=True)\nclass Base:\n    """A base."""\n\n    slug: str\n\n\n'
        '@dataclass(frozen=True)\nclass Story(Base):\n    """A story."""\n\n    t: str\n'
    ),
}

FORBIDDEN = {
    "a pydantic model": 'class Story(BaseModel):\n    """A story."""\n\n    slug: str\n',
    "a local base that is a model": (
        'class Authored(BaseModel):\n    """A base."""\n\n\n'
        'class Story(Authored):\n    """A story."""\n\n    slug: str\n'
    ),
    "a pydantic dataclass": (
        '@pydantic_dataclass(frozen=True)\nclass Story:\n    """A story."""\n\n'
        "    slug: str\n"
    ),
    "a dataclass that is not frozen": (
        '@dataclass\nclass Story:\n    """A story."""\n\n    slug: str\n'
    ),
    "a plain class": 'class Story:\n    """A story."""\n\n    slug: str\n',
    "a tuple subclass": 'class Story(tuple):\n    """Immutable, and not a category."""\n',
    "a frozenset subclass": 'class Story(frozenset):\n    """Also not a category."""\n',
}


def a_domain_context(tmp_path: Path, body: str) -> Path:
    """Write an importable context whose domain holds one declaration."""
    package = f"ring{next(_UNIQUE)}"
    root = tmp_path / package
    context = root / package / "stories"
    (context / "domain" / "models").mkdir(parents=True)
    (root / package / "__init__.py").write_text("")
    (context / "__init__.py").write_text('"""Stories."""\n')
    (context / "domain" / "__init__.py").write_text("")
    (context / "domain" / "models" / "__init__.py").write_text("")
    (context / "domain" / "models" / "story.py").write_text(PREAMBLE + body)
    sys.path.insert(0, str(root))
    return context


def objections(tmp_path: Path, body: str) -> list[str]:
    """What the rule says about the Story that body declares."""
    context = a_domain_context(tmp_path, body)
    return entities_that_are_not_frozen_dataclasses(
        entity_verdicts("stories", context, ["Story"])
    )


def test_a_domain_class_must_be_a_frozen_stdlib_dataclass(tmp_path: Path) -> None:
    """The rule accepts what the domain may be and refuses the rest.

    Every case is tried before reporting, so a failure names all of
    them.
    """
    refused = [what for what, body in ALLOWED.items() if objections(tmp_path, body)]
    assert not refused, "refused a domain class: " + ", ".join(refused)

    leaked = [
        what for what, body in FORBIDDEN.items() if not objections(tmp_path, body)
    ]
    assert not leaked, "accepted a class the domain may not hold: " + ", ".join(leaked)


def test_the_objection_names_the_context_the_class_and_the_reason(
    tmp_path: Path,
) -> None:
    """So an author can act on it without rerunning anything."""
    assert objections(tmp_path, FORBIDDEN["a pydantic model"]) == [
        "stories.Story: it is a pydantic model. A domain class is a frozen dataclass"
    ]


def test_a_pydantic_dataclass_says_which_decorator_to_change(tmp_path: Path) -> None:
    """The edit is the import, not the shape."""
    objection = objections(tmp_path, FORBIDDEN["a pydantic dataclass"])[0]

    assert "pydantic dataclass" in objection


def test_the_frozen_rule_passes_what_this_one_catches() -> None:
    """Why this rule exists, pinned so it cannot be quietly removed.

    entities_not_extending_Entity reads the decorator, and both
    decorators are spelled @dataclass(frozen=True).
    """
    story = ClassInfo(
        name="Story",
        file="domain/models/story.py",
        decorators=("pydantic.dataclasses.dataclass",),
        decorator_arguments={"dataclass": {"frozen": "True"}},
    )

    assert entities_not_extending_Entity([("hcd", story)]) == []
