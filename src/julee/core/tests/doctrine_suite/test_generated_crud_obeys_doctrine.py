"""The CRUD generator's output, held to the doctrine it lands in.

Every kit's generated CRUD is written by one function here, so a rule
the generator breaks is broken identically in every kit that adopts it.
Nothing was checking that: the generator's own tests import the module
and run the use cases, which says the code works and nothing about
where its pydantic lives.

This generates into a solution and runs the doctrine over it.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from julee.core.usecases.generate_crud import generate

from .harness import a_julee_solution, assert_doctrine_ran, run_doctrine

pytestmark = pytest.mark.unit

USE_CASE_TEST = "src/julee/core/doctrine/test_use_case.py"
SELECTOR = "pydantic_DTO or import_only_inward or import_another_usecase"
EXPECTED_TESTS = 4
"""The rules that bear on generated code: both DTO tests, and both
about what a use case may import. The driven-port and domain rules
judge what the kit wrote, not what the generator emitted."""

ENTITY = '''"""The Story entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    """A unit of work."""

    slug: str
    title: str = ""
'''

REPOSITORY = '''"""Where stories are kept."""

from typing import Protocol

from acme.stories.domain.models.story import Story


class StoryRepository(Protocol):
    """Stories, stored somewhere."""

    async def get(self, entity_id: str) -> Story | None: ...

    async def save(self, entity: Story) -> None: ...

    async def list_all(self) -> list[Story]: ...

    async def delete(self, entity_id: str) -> bool: ...
'''


def a_solution_with_generated_crud(root: Path) -> Path:
    """Write a solution and generate its CRUD into it.

    Args:
        root: The solution root to write into

    Returns:
        The root, ready to pass as JULEE_TARGET
    """
    context = a_julee_solution(root)
    (context / "domain" / "models").mkdir(parents=True)
    (context / "domain" / "repositories").mkdir(parents=True)
    (context / "usecases").mkdir(parents=True)
    for package in (
        context / "domain",
        context / "domain" / "models",
        context / "domain" / "repositories",
        context / "usecases",
    ):
        (package / "__init__.py").write_text("")
    (context / "domain" / "models" / "story.py").write_text(ENTITY)
    (context / "domain" / "repositories" / "story.py").write_text(REPOSITORY)

    generate(
        entity="Story",
        entity_module="acme.stories.domain.models.story",
        repo="StoryRepository",
        repo_module="acme.stories.domain.repositories.story",
        id_field="slug",
        create_fields=[("slug", "str"), ("title", 'str=""')],
        update_fields=[("title", "str")],
        include_delete=True,
        out_dir=context / "usecases",
    )
    return root


def test_generated_crud_obeys_the_doctrine_it_lands_in(tmp_path: Path) -> None:
    """What the generator writes must pass the rules a kit is held to.

    The kits inherit whatever this emits. Six of c4's twelve import
    objections and seven of hcd's come from generated files, so the
    fix belongs here and not in any kit.
    """
    result = run_doctrine(
        a_solution_with_generated_crud(tmp_path / "generated"),
        USE_CASE_TEST,
        SELECTOR,
    )

    assert_doctrine_ran(result, EXPECTED_TESTS, SELECTOR)
    assert result.returncode == 0, (
        f"the generator emitted code that breaks doctrine:\n{result.stdout}"
    )


def test_the_generated_use_case_module_imports_no_pydantic(tmp_path: Path) -> None:
    """Named separately because it is the whole point.

    A use case speaks the domain. The messages it takes and returns are
    pydantic and live apart from it.
    """
    root = a_solution_with_generated_crud(tmp_path / "no-pydantic")
    emitted = (
        root / "src" / "acme" / "stories" / "usecases" / "crud_story.py"
    ).read_text()

    assert "pydantic" not in emitted, (
        "the generated use case module imports pydantic:\n"
        + "\n".join(line for line in emitted.splitlines() if "pydantic" in line)
    )


def test_the_generated_use_case_does_not_call_pydantic(tmp_path: Path) -> None:
    """model_dump inside execute() is business logic in pydantic's words.

    'the fields the caller actually named' is a domain meaning, and
    exclude_unset is not how the domain says it.
    """
    root = a_solution_with_generated_crud(tmp_path / "no-model-dump")
    emitted = (
        root / "src" / "acme" / "stories" / "usecases" / "crud_story.py"
    ).read_text()

    for called in ("model_dump", "model_validate", "model_copy"):
        assert called not in emitted, f"the generated use case calls {called}()"


def test_python_can_still_run_what_it_wrote(tmp_path: Path) -> None:
    """The generated module must import, whatever shape it is in.

    The doctrine run would skip a file it cannot parse, so this asks
    Python directly rather than trusting a green doctrine.
    """
    root = a_solution_with_generated_crud(tmp_path / "importable")
    result = subprocess.run(
        [sys.executable, "-c", "import acme.stories.usecases.crud_story"],
        cwd=root / "src",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
