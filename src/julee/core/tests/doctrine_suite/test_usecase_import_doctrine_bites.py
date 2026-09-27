"""The use case import doctrine, run against solutions on disk.

The tests in doctrine_rules/ check rule functions. This one runs the
doctrine suite itself as a subprocess and asserts the outcome, so it
fails if the suite stops objecting.
"""

import subprocess
from pathlib import Path

import pytest

from .harness import a_julee_solution, assert_doctrine_ran, run_doctrine

pytestmark = pytest.mark.unit

IMPORT_TEST = "src/julee/core/doctrine/test_use_case.py"
IMPORT_SELECTOR = "import_only_inward"
EXPECTED_IMPORT_TESTS = 1

ENTITY = '''"""The Story entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    """A unit of work."""

    slug: str
'''

PORT = '''"""The Story repository."""

from typing import Protocol

from acme.stories.domain.models.story import Story


class StoryRepository(Protocol):
    """Stories, stored somewhere."""

    async def get(self, slug: str) -> Story | None: ...
'''

DTOS = '''"""The messages this use case takes and returns."""

from pydantic import BaseModel, ConfigDict


class GetStoryRequest(BaseModel):
    """Which story to fetch."""

    model_config = ConfigDict(frozen=True)

    slug: str


class GetStoryResponse(BaseModel):
    """The story that was found."""

    model_config = ConfigDict(frozen=True)

    title: str
'''
"""Pydantic lives here and nowhere else inside a bounded context."""

ADAPTER = '''"""A repository that keeps stories in memory."""


class MemoryStoryRepository:
    """Not something a use case may reach for."""
'''

ALLOWED = {
    "its own domain models": "from acme.stories.domain.models.story import Story",
    "its own ports": (
        "from acme.stories.domain.repositories.story import StoryRepository"
    ),
    "its own dtos": "from acme.stories.dtos.get_story import GetStoryRequest",
    "its own dtos relatively": "from ..dtos.get_story import GetStoryResponse",
    "a sibling use case by name": "from acme.stories.usecases.other import OtherUseCase",
    "a sibling use case relatively": "from .other import OtherUseCase",
    "its own domain relatively": "from ..domain.models.story import Story",
    "dataclasses": "from dataclasses import replace",
    "datetime": "from datetime import datetime",
    "typing": "from typing import Protocol",
    "collections.abc": "from collections.abc import Sequence",
    "enum": "from enum import StrEnum",
    "uuid": "from uuid import UUID",
    "decimal": "from decimal import Decimal",
    "future annotations": "from __future__ import annotations",
    "julee's kernel entities": "from julee.core.entities.text import Slug",
    "julee's use case bases": "from julee.core.usecases import generic_crud",
}
"""What a use case may reach for."""

FORBIDDEN = {
    "pydantic": ("from pydantic import BaseModel", "pydantic"),
    "a third-party package": ("import yaml", "yaml"),
    "json": ("import json", "json"),
    "io": ("import io", "io"),
    "logging": ("import logging", "logging"),
    "os": ("import os", "os"),
    "asyncio": ("import asyncio", "asyncio"),
    "random": ("import random", "random"),
    "time": ("import time", "time"),
    "hashlib": ("import hashlib", "hashlib"),
    "collections": ("import collections", "collections"),
    "pathlib": ("from pathlib import Path", "pathlib"),
    "its own infrastructure": (
        "from acme.stories.infrastructure.memory import MemoryStoryRepository",
        "acme.stories.infrastructure.memory",
    ),
    "its own infrastructure relatively": (
        "from ..infrastructure.other import Other",
        "acme.stories.infrastructure.other",
    ),
    "julee's adapters": (
        "from julee.repositories.memory.base import MemoryRepositoryMixin",
        "julee.repositories.memory.base",
    ),
    "julee's integrations": (
        "from julee.integrations.temporal import clock",
        "julee.integrations.temporal",
    ),
    "an import deferred inside a block": (
        "if True:\n    import csv  # deferred, and still an import",
        "csv",
    ),
}
"""What a use case may not reach for, with the module each must name.

Keyed by what is wrong, so one module carries them all and the
objections can be told apart in one run.
"""


def a_usecase_module(imports: tuple[str, ...]) -> str:
    """A use case module making the given imports."""
    body = "\n".join(imports)
    return (
        f'"""Get a story."""\n\n{body}\n\n\n'
        "class GetStoryRequest:\n"
        '    """Which story."""\n\n\n'
        "class GetStoryResponse:\n"
        '    """The story."""\n\n\n'
        "class GetStoryUseCase:\n"
        '    """Fetch one story by its slug."""\n\n'
        "    async def execute(self, request: GetStoryRequest) -> GetStoryResponse:\n"
        '        """Fetch it."""\n'
        "        raise NotImplementedError\n"
    )


def a_solution(root: Path, imports: tuple[str, ...]) -> Path:
    """Write a julee solution whose use case makes those imports.

    Args:
        root: The solution root to write into
        imports: Import statements for usecases/get_story.py

    Returns:
        The root, ready to pass as JULEE_TARGET
    """
    context = a_julee_solution(root)
    (context / "domain" / "models").mkdir(parents=True)
    (context / "domain" / "repositories").mkdir(parents=True)
    (context / "infrastructure").mkdir(parents=True)
    (context / "dtos").mkdir(parents=True)
    (context / "usecases").mkdir(parents=True)
    for package in (
        context / "domain",
        context / "domain" / "models",
        context / "domain" / "repositories",
        context / "infrastructure",
        context / "dtos",
        context / "usecases",
    ):
        (package / "__init__.py").write_text("")
    # A package init doing a relative import: its own package is the
    # package, not the one above, and getting that wrong made every
    # relative import in an __init__ resolve one level too high.
    (context / "usecases" / "__init__.py").write_text(
        'from .other import OtherUseCase\n\n__all__ = ["OtherUseCase"]\n'
    )
    (context / "domain" / "models" / "story.py").write_text(ENTITY)
    (context / "domain" / "repositories" / "story.py").write_text(PORT)
    (context / "dtos" / "get_story.py").write_text(DTOS)
    (context / "infrastructure" / "memory.py").write_text(ADAPTER)
    (context / "infrastructure" / "other.py").write_text(
        '"""Another adapter."""\n\n\nclass Other:\n    """Not for a use case."""\n'
    )
    (context / "usecases" / "other.py").write_text(
        '"""Another use case."""\n\n\nclass OtherUseCase:\n    """Another."""\n'
    )
    (context / "usecases" / "get_story.py").write_text(a_usecase_module(imports))
    return root


def run_import_doctrine(target: Path) -> subprocess.CompletedProcess[str]:
    """Run the use case import doctrine against a solution."""
    return run_doctrine(target, IMPORT_TEST, IMPORT_SELECTOR)


def test_a_usecase_may_import_only_inward(tmp_path: Path) -> None:
    """The doctrine passes what points inward and fails everything else.

    Every case runs before reporting, so a failure names all of them.
    """
    good = run_import_doctrine(a_solution(tmp_path / "good", tuple(ALLOWED.values())))
    assert_doctrine_ran(good, EXPECTED_IMPORT_TESTS, IMPORT_SELECTOR)
    assert good.returncode == 0, (
        f"doctrine refused a use case importing only inward:\n{good.stdout}"
    )

    bad = run_import_doctrine(
        a_solution(
            tmp_path / "bad",
            tuple(statement for statement, _ in FORBIDDEN.values()),
        )
    )
    assert_doctrine_ran(bad, EXPECTED_IMPORT_TESTS, IMPORT_SELECTOR)
    assert bad.returncode != 0, f"doctrine passed all of them:\n{bad.stdout}"

    missed = [
        what
        for what, (_, module) in FORBIDDEN.items()
        if f"imports {module}," not in bad.stdout
    ]
    assert not missed, "the doctrine suite did not object to: " + ", ".join(missed)
