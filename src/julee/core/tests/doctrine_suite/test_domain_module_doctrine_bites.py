"""What doctrine does with a module under domain/, run against real solutions.

Every module under domain/ is read (ADR 024). One named for a kind
holds that kind, as a directory of the name does; ``errors`` is the
kind for the exceptions a domain declares; and any other module is
read as entities, directly under domain/ as much as in an area.

Until that, a module directly under domain/ was read by nothing, and a
bounded context had nowhere to declare an exception that doctrine would
not object to.
"""

from pathlib import Path

import pytest

from .harness import a_solution_holding, assert_doctrine_ran, run_doctrine

pytestmark = pytest.mark.unit

ENTITY_TEST = "src/julee/core/doctrine/test_entity.py"
ERRORS_TEST = "src/julee/core/doctrine/test_errors.py"
PORT_TEST = "src/julee/core/doctrine/test_driven_port.py"

ENTITY_SELECTOR = "MUST_be_frozen_dataclasses"
ERRORS_SELECTOR = "errors_MUST_be_an_exception"

A_FROZEN_ENTITY = '''"""A story, which is kept under an id."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    """A unit of work."""

    slug: str
'''

A_PYDANTIC_ENTITY = '''"""A story, written as a message would be."""

from pydantic import BaseModel


class Story(BaseModel):
    """A unit of work."""

    slug: str
'''

THE_BASE_ERRORS = '''"""What every refusal in this context is built on."""


class NotFound(LookupError):
    """Something asked for is not there."""
'''

AN_AREAS_ERRORS = '''"""What planning refuses."""

from acme.stories.domain.errors import NotFound


class StoryNotFound(NotFound):
    """No story has that slug."""

    def __init__(self, slug: str) -> None:
        super().__init__(f"No story called {slug}")
        self.slug = slug
'''

NOT_AN_ERROR = '''"""Something in errors that is not an exception."""


class StoryHelper:
    """Raises nothing and cannot be raised."""
'''

AN_ENTITY_AND_ITS_ERROR = (
    A_FROZEN_ENTITY
    + '''

class StoryNotFound(LookupError):
    """No story has that slug."""
'''
)

A_REPOSITORY = '''"""Where stories are kept."""

from typing import Any, Protocol

from acme.stories.domain.story import Story


class StoryRepository(Protocol):
    """Keeps stories."""

    async def get(self, slug: str) -> {returns}: ...
'''

AN_ORACLE = '''"""Something fetched from outside."""

from typing import Protocol


class {name}(Protocol):
    """Fetches a reading."""

    async def fetch(self, url: str) -> str: ...
'''


A_HANDLER = '''"""What is told when a story is planned."""

from typing import Protocol


class StoryPlannedHandler(Protocol):
    """Told that a story was planned."""

    async def handle(self, slug: str) -> None: ...
'''


class TestAModuleDirectlyUnderDomain:
    def test_it_is_held_to_what_an_entity_must_be(self, tmp_path: Path) -> None:
        good = run_doctrine(
            a_solution_holding(tmp_path / "good", {"domain/story.py": A_FROZEN_ENTITY}),
            ENTITY_TEST,
            ENTITY_SELECTOR,
        )
        bad = run_doctrine(
            a_solution_holding(
                tmp_path / "bad", {"domain/story.py": A_PYDANTIC_ENTITY}
            ),
            ENTITY_TEST,
            ENTITY_SELECTOR,
        )

        assert_doctrine_ran(good, 1, ENTITY_SELECTOR)
        assert good.returncode == 0, (
            "doctrine objected to a frozen dataclass directly under domain/:\n"
            + good.stdout
        )
        assert_doctrine_ran(bad, 1, ENTITY_SELECTOR)
        assert bad.returncode != 0, (
            "doctrine did not object to a pydantic model directly under "
            "domain/:\n" + bad.stdout
        )
        assert "Story" in bad.stdout

    def test_a_context_with_nothing_else_is_found(self, tmp_path: Path) -> None:
        """No domain/models/ and no use case: the module is the domain."""
        root = a_solution_holding(tmp_path, {"domain/story.py": A_PYDANTIC_ENTITY})
        (root / "src" / "acme" / "stories" / "usecases" / "__init__.py").unlink()
        (root / "src" / "acme" / "stories" / "usecases").rmdir()

        result = run_doctrine(root, ENTITY_TEST, ENTITY_SELECTOR)

        assert_doctrine_ran(result, 1, ENTITY_SELECTOR)
        assert result.returncode != 0, (
            "doctrine did not find a bounded context whose domain is one "
            "module:\n" + result.stdout
        )
        assert "Story" in result.stdout


class TestErrors:
    def test_an_exception_in_errors_is_what_belongs_there(self, tmp_path: Path) -> None:
        """In a module under domain/, a module in an area and a
        directory, one built on another across them."""
        root = a_solution_holding(
            tmp_path,
            {
                "domain/errors.py": THE_BASE_ERRORS,
                "domain/planning/errors.py": AN_AREAS_ERRORS,
                "domain/planning/story.py": A_FROZEN_ENTITY,
                "domain/reviewing/errors/refusals.py": AN_AREAS_ERRORS.replace(
                    "StoryNotFound", "ReviewNotFound"
                ),
            },
        )

        errors = run_doctrine(root, ERRORS_TEST, ERRORS_SELECTOR)
        entities = run_doctrine(root, ENTITY_TEST, ENTITY_SELECTOR)

        assert_doctrine_ran(errors, 1, ERRORS_SELECTOR)
        assert errors.returncode == 0, (
            "doctrine objected to an exception in errors:\n" + errors.stdout
        )
        assert_doctrine_ran(entities, 1, ENTITY_SELECTOR)
        assert entities.returncode == 0, (
            "doctrine read an exception in errors as an entity:\n" + entities.stdout
        )

    @pytest.mark.parametrize(
        "where",
        ["domain/errors.py", "domain/planning/errors.py", "domain/errors/planning.py"],
    )
    def test_a_class_in_errors_that_is_no_exception_is_objected_to(
        self, tmp_path: Path, where: str
    ) -> None:
        result = run_doctrine(
            a_solution_holding(
                tmp_path,
                {"domain/models/story.py": A_FROZEN_ENTITY, where: NOT_AN_ERROR},
            ),
            ERRORS_TEST,
            ERRORS_SELECTOR,
        )

        assert_doctrine_ran(result, 1, ERRORS_SELECTOR)
        assert result.returncode != 0, (
            f"doctrine did not object to a plain class in {where}:\n" + result.stdout
        )
        assert "StoryHelper" in result.stdout

    def test_an_exception_among_the_entities_is_told_where_it_belongs(
        self, tmp_path: Path
    ) -> None:
        result = run_doctrine(
            a_solution_holding(
                tmp_path, {"domain/planning/story.py": AN_ENTITY_AND_ITS_ERROR}
            ),
            ENTITY_TEST,
            ENTITY_SELECTOR,
        )

        assert_doctrine_ran(result, 1, ENTITY_SELECTOR)
        assert result.returncode != 0, (
            "doctrine did not object to an exception declared beside an "
            "entity:\n" + result.stdout
        )
        assert "StoryNotFound" in result.stdout
        assert "belongs in errors" in " ".join(result.stdout.split())


class TestAModuleNamedForAPort:
    def test_it_is_held_to_what_may_cross_a_port(self, tmp_path: Path) -> None:
        selector = "only_domain_types"
        files = {"domain/story.py": A_FROZEN_ENTITY}

        good = run_doctrine(
            a_solution_holding(
                tmp_path / "good",
                {
                    **files,
                    "domain/repositories.py": A_REPOSITORY.format(
                        returns="Story | None"
                    ),
                },
            ),
            PORT_TEST,
            selector,
        )
        bad = run_doctrine(
            a_solution_holding(
                tmp_path / "bad",
                {**files, "domain/repositories.py": A_REPOSITORY.format(returns="Any")},
            ),
            PORT_TEST,
            selector,
        )

        assert_doctrine_ran(good, 1, selector)
        assert good.returncode == 0, (
            "doctrine objected to a repository in domain/repositories.py that "
            "speaks only the domain:\n" + good.stdout
        )
        assert_doctrine_ran(bad, 1, selector)
        assert bad.returncode != 0, (
            "doctrine did not object to a repository in domain/repositories.py "
            "returning Any:\n" + bad.stdout
        )
        assert "StoryRepository" in bad.stdout

    def test_it_must_claim_the_role_its_name_offers(self, tmp_path: Path) -> None:
        selector = "claim_a_role"

        good = run_doctrine(
            a_solution_holding(
                tmp_path / "good",
                {"domain/oracles.py": AN_ORACLE.format(name="ReadingOracle")},
            ),
            PORT_TEST,
            selector,
        )
        bad = run_doctrine(
            a_solution_holding(
                tmp_path / "bad",
                {"domain/oracles.py": AN_ORACLE.format(name="ReadingFetcher")},
            ),
            PORT_TEST,
            selector,
        )

        assert_doctrine_ran(good, 1, selector)
        assert good.returncode == 0, (
            "doctrine objected to an oracle named as one in domain/oracles.py:\n"
            + good.stdout
        )
        assert_doctrine_ran(bad, 1, selector)
        assert bad.returncode != 0, (
            "doctrine did not object to a protocol in domain/oracles.py that "
            "claims no role:\n" + bad.stdout
        )
        assert "ReadingFetcher" in bad.stdout

    def test_it_is_a_place_a_port_may_be_declared(self, tmp_path: Path) -> None:
        selector = "declared_or_implemented_nowhere_else"

        result = run_doctrine(
            a_solution_holding(
                tmp_path,
                {"domain/oracles.py": AN_ORACLE.format(name="ReadingOracle")},
            ),
            PORT_TEST,
            selector,
        )

        assert_doctrine_ran(result, 1, selector)
        assert result.returncode == 0, (
            "doctrine objected to an oracle declared in domain/oracles.py:\n"
            + result.stdout
        )

    def test_a_handlers_module_is_read_and_fails_the_one_to_a_file_rule(
        self, tmp_path: Path
    ) -> None:
        """A handler protocol sits in a file named *_handler.py, which a
        module called handlers is not. ADR 024 says so; this holds it to
        that, and shows the module is read."""
        selector = "singular_handler_file"
        handler_test = "src/julee/core/doctrine/test_handler_protocol.py"

        in_its_own_file = run_doctrine(
            a_solution_holding(
                tmp_path / "file",
                {"domain/handlers/story_planned_handler.py": A_HANDLER},
            ),
            handler_test,
            selector,
        )
        in_a_module = run_doctrine(
            a_solution_holding(tmp_path / "module", {"domain/handlers.py": A_HANDLER}),
            handler_test,
            selector,
        )

        assert_doctrine_ran(in_its_own_file, 1, selector)
        assert in_its_own_file.returncode == 0, (
            "doctrine objected to a handler in its own file:\n" + in_its_own_file.stdout
        )
        assert_doctrine_ran(in_a_module, 1, selector)
        assert in_a_module.returncode != 0, (
            "doctrine did not object to a handler in domain/handlers.py:\n"
            + in_a_module.stdout
        )
        assert "StoryPlannedHandler" in in_a_module.stdout
