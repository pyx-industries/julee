"""Solutions written to disk for the census tests.

Two bounded contexts under one search root. ``stories`` is laid out as
julee prescribes and holds one of everything the census has a word for.
``engagements`` keeps its entity and its repository in an area under
``domain/``, which julee reads (ADR 023). It also departs from the
layout: its use cases share a module and carry no suffix, which leaves
them use cases the naming rule would object to, and one port is at the
top level, which leaves it in no family. That much is here to show what
the census reports for such source, not to say julee supports it.

The sources are short so that every line number in a test can be
checked against them by eye.
"""

from pathlib import Path

__all__ = ["SEARCH_ROOT", "a_solution", "write"]

SEARCH_ROOT = "src/acme"

STORIES = {
    "domain/models/story.py": '''"""A story."""

from dataclasses import dataclass
from typing import NewType

StoryId = NewType("StoryId", str)


def new_story_id() -> StoryId:
    return StoryId("s")


@dataclass(frozen=True)
class Story:
    """A unit of work."""

    slug: str
''',
    "domain/models/_draft.py": '''"""In a module whose name hides nothing."""


class Draft:
    """Half a story."""
''',
    "domain/values/score.py": '''"""A score."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Score:
    """How well something did."""

    points: int
''',
    "domain/repositories/story.py": '''"""Where stories are kept."""

from typing import Protocol


class StoryRepository(Protocol):
    """Keeps stories."""

    async def get(self, slug: str) -> object: ...
''',
    "dtos/story.py": '''"""Messages about stories."""

from pydantic import BaseModel


class PlanStoryRequest(BaseModel):
    """What planning takes."""


class PlanStoryResponse(BaseModel):
    """What planning returns."""


class StoryMessage(BaseModel):
    """A story on the wire."""
''',
    "dtos/crud_story.py": '''"""One declaration of a request."""

from pydantic import BaseModel


class GetStoryRequest(BaseModel):
    """One way to ask."""
''',
    "dtos/get_story.py": '''"""Another declaration of the same name."""

from pydantic import BaseModel


class GetStoryRequest(BaseModel):
    """Another way to ask."""
''',
    "usecases/plan_story.py": '''"""Planning a story."""

from acme.stories.dtos.crud_story import GetStoryRequest
from acme.stories.dtos.story import PlanStoryRequest, PlanStoryResponse
from elsewhere.dtos import ArchiveStoryResponse


class PlanStoryUseCase:
    """Plans a story."""

    async def execute(self, request: PlanStoryRequest) -> PlanStoryResponse:
        return PlanStoryResponse()


class StoryHelpers:
    """No suffix, and a use case to doctrine all the same."""


class TestDouble:
    """Named like a test, in a file that is not one, so it is read."""
''',
    "infrastructure/memory.py": '''"""Stories kept in memory."""


class MemoryStoryRepository:
    """Keeps stories in a dict."""
''',
    "tests/test_story.py": '''"""A test, which the census does not read."""


class TestStory:
    pass
''',
}

ENGAGEMENTS = {
    "usecases/engagement.py": '''"""Everything about engagements, in one module."""


class BaseEngagementUseCase:
    """Wiring only."""

    def __init__(self, repository: object) -> None:
        self.repository = repository


class RecordEngagement(BaseEngagementUseCase):
    def execute(self, user: object, request: object) -> object: ...


class GetEngagement(BaseEngagementUseCase):
    def execute(self, user: object, engagement_id: object) -> object: ...


class SearchEngagements(BaseEngagementUseCase):
    def execute(self, user: object, criteria: object) -> object: ...


class ListEngagementFilters(BaseEngagementUseCase):
    def execute(self, user: object) -> object: ...
''',
    "domain/engagement/engagement.py": '''"""An engagement, in an area of its own."""

from dataclasses import dataclass
from typing import NewType

EngagementId = NewType("EngagementId", str)


@dataclass(frozen=True)
class Engagement:
    """A visit."""

    id: EngagementId
''',
    "domain/engagement/repositories/engagement.py": '''"""A port, in the area's repositories directory."""

from typing import Protocol


class EngagementRepository(Protocol):
    def get(self, engagement_id: object) -> object: ...
''',
    "ports/clock.py": '''"""A port at the top level."""

from typing import Protocol


class ClockService(Protocol):
    def now(self) -> object: ...
''',
}

OUTSIDE = {
    "shared/__init__.py": "",
    "shared/util.py": '''"""Under a reserved name."""


def slugify(text: str) -> str:
    return text.lower()
''',
    "tools/__init__.py": "",
    "tools/helper.py": '''"""A package with no domain and no use cases."""


class Helper:
    pass
''',
    "scripts/run.py": '''"""Not in a package at all."""


def main() -> None:
    pass
''',
}


def write(directory: Path, files: dict[str, str]) -> None:
    """Write files under a directory, making directories as needed.

    Args:
        directory: Where the paths are relative to
        files: Path to content
    """
    for path, content in files.items():
        target = directory / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)


def _packages(context: Path, files: dict[str, str]) -> None:
    """Make every directory holding one of the files a package."""
    for path in files:
        directory = (context / path).parent
        while directory != context.parent:
            init = directory / "__init__.py"
            if not init.exists():
                init.write_text("")
            directory = directory.parent


def a_solution(root: Path) -> Path:
    """Write the two contexts and the source that is in neither.

    Args:
        root: The solution root to write into

    Returns:
        The root, with ``src/acme`` as its search root
    """
    source = root / SEARCH_ROOT
    source.mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "acme"\nversion = "0.1.0"\n\n'
        f'[tool.julee]\nsearch_root = "{SEARCH_ROOT}"\n'
    )
    (source / "__init__.py").write_text('"""Acme."""\n')

    for slug, files in (("stories", STORIES), ("engagements", ENGAGEMENTS)):
        write(source / slug, files)
        _packages(source / slug, files)
    write(source, OUTSIDE)
    return root
