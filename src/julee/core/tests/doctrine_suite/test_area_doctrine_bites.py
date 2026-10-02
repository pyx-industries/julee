"""What doctrine does with an area under domain/, run against real solutions.

A directory under domain/ whose name is not a kind's is an area: a
module it holds is read as entities, and a kind directory inside it is
read as that kind (ADR 023). Until that, such a directory was read by
nothing, and the one rule that noticed said only that it was there.

So what is tested is that the rules reach into an area: each case is a
class that would be objected to in domain/models/ or domain/oracles/,
written in an area instead.
"""

from pathlib import Path

import pytest

from .harness import a_solution_holding as a_solution
from .harness import assert_doctrine_ran, run_doctrine

pytestmark = pytest.mark.unit

ENTITY_TEST = "src/julee/core/doctrine/test_entity.py"
PORT_TEST = "src/julee/core/doctrine/test_driven_port.py"

A_FROZEN_ENTITY = '''"""A story, which is kept under an id."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    """A unit of work."""

    slug: str
'''

AN_UNFROZEN_ENTITY = A_FROZEN_ENTITY.replace("@dataclass(frozen=True)", "@dataclass")

A_PYDANTIC_ENTITY = '''"""A story, written as a message would be."""

from pydantic import BaseModel


class Story(BaseModel):
    """A unit of work."""

    slug: str
'''

A_REPOSITORY = '''"""Where stories are kept."""

from typing import Any, Protocol

from acme.stories.domain.planning.story import Story


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

AN_ORACLE_NAMING_THE_ENTITY = '''"""An oracle, which must be bound to no entity."""

from typing import Protocol

from acme.stories.domain.planning.story import Story


class ReadingOracle(Protocol):
    """Fetches something from outside."""

    async def fetch(self, url: str) -> Story: ...
'''

A_USE_CASE = '''"""Planning a story."""


class PlanStoryUseCase:
    """Plans a story."""

    async def execute(self, request: object) -> object: ...
'''


class TestAnEntityInAnArea:
    def test_it_is_held_to_what_an_entity_must_be(self, tmp_path: Path) -> None:
        """The rule that imports the class and asks Python what it is."""
        selector = "MUST_be_frozen_dataclasses"

        good = run_doctrine(
            a_solution(
                tmp_path / "good", {"domain/planning/story.py": A_FROZEN_ENTITY}
            ),
            ENTITY_TEST,
            selector,
        )
        bad = run_doctrine(
            a_solution(
                tmp_path / "bad", {"domain/planning/story.py": A_PYDANTIC_ENTITY}
            ),
            ENTITY_TEST,
            selector,
        )

        assert_doctrine_ran(good, 1, selector)
        assert good.returncode == 0, (
            "doctrine objected to a frozen dataclass in an area:\n" + good.stdout
        )
        assert_doctrine_ran(bad, 1, selector)
        assert bad.returncode != 0, (
            "doctrine did not object to a pydantic model in an area:\n" + bad.stdout
        )
        assert "Story" in bad.stdout

    def test_it_is_held_to_immutability(self, tmp_path: Path) -> None:
        """The rule that reads the class from its source."""
        selector = "entity_classes_MUST_be_immutable"

        result = run_doctrine(
            a_solution(tmp_path, {"domain/planning/story.py": AN_UNFROZEN_ENTITY}),
            ENTITY_TEST,
            selector,
        )

        assert_doctrine_ran(result, 1, selector)
        assert result.returncode != 0, (
            "doctrine did not object to an entity in an area that can be "
            "mutated:\n" + result.stdout
        )
        assert "Story" in result.stdout

    def test_a_context_keeping_every_entity_in_an_area_is_not_blind(
        self, tmp_path: Path
    ) -> None:
        """It has use cases, and doctrine can see what they work on."""
        selector = "MUST_yield_entities"

        result = run_doctrine(
            a_solution(
                tmp_path,
                {
                    "domain/planning/story.py": A_FROZEN_ENTITY,
                    "usecases/plan_story.py": A_USE_CASE,
                },
            ),
            ENTITY_TEST,
            selector,
        )

        assert_doctrine_ran(result, 1, selector)
        assert result.returncode == 0, (
            "doctrine read no entity out of a context that keeps them in "
            "an area:\n" + result.stdout
        )

    def test_it_counts_as_an_entity_to_the_rules_about_ports(
        self, tmp_path: Path
    ) -> None:
        """An oracle may name no entity, and one kept in an area is one."""
        selector = "name_no_entity"

        result = run_doctrine(
            a_solution(
                tmp_path,
                {
                    "domain/planning/story.py": A_FROZEN_ENTITY,
                    "domain/oracles/reading.py": AN_ORACLE_NAMING_THE_ENTITY,
                },
            ),
            PORT_TEST,
            selector,
        )

        assert_doctrine_ran(result, 1, selector)
        assert result.returncode != 0, (
            "doctrine did not object to an oracle bound to an entity kept "
            "in an area:\n" + result.stdout
        )
        assert "Story" in result.stdout


class TestAPortInAnArea:
    def test_it_is_held_to_what_may_cross_a_port(self, tmp_path: Path) -> None:
        selector = "only_domain_types"
        files = {"domain/planning/story.py": A_FROZEN_ENTITY}
        port = "domain/planning/repositories/story.py"

        good = run_doctrine(
            a_solution(
                tmp_path / "good",
                {**files, port: A_REPOSITORY.format(returns="Story | None")},
            ),
            PORT_TEST,
            selector,
        )
        bad = run_doctrine(
            a_solution(
                tmp_path / "bad", {**files, port: A_REPOSITORY.format(returns="Any")}
            ),
            PORT_TEST,
            selector,
        )

        assert_doctrine_ran(good, 1, selector)
        assert good.returncode == 0, (
            "doctrine objected to a repository in an area that speaks only "
            "the domain:\n" + good.stdout
        )
        assert_doctrine_ran(bad, 1, selector)
        assert bad.returncode != 0, (
            "doctrine did not object to a repository in an area returning "
            "Any:\n" + bad.stdout
        )
        assert "StoryRepository" in bad.stdout

    def test_it_must_claim_the_role_its_directory_offers(self, tmp_path: Path) -> None:
        selector = "claim_a_role"
        port = "domain/planning/oracles/reading.py"

        good = run_doctrine(
            a_solution(
                tmp_path / "good", {port: AN_ORACLE.format(name="ReadingOracle")}
            ),
            PORT_TEST,
            selector,
        )
        bad = run_doctrine(
            a_solution(
                tmp_path / "bad", {port: AN_ORACLE.format(name="ReadingFetcher")}
            ),
            PORT_TEST,
            selector,
        )

        assert_doctrine_ran(good, 1, selector)
        assert good.returncode == 0, (
            "doctrine objected to an oracle named as one in an area:\n" + good.stdout
        )
        assert_doctrine_ran(bad, 1, selector)
        assert bad.returncode != 0, (
            "doctrine did not object to a protocol in an area's oracles/ "
            "that claims no role:\n" + bad.stdout
        )
        assert "ReadingFetcher" in bad.stdout

    def test_its_directory_is_a_place_a_port_may_be_declared(
        self, tmp_path: Path
    ) -> None:
        selector = "declared_or_implemented_nowhere_else"

        in_an_area = run_doctrine(
            a_solution(
                tmp_path / "area",
                {
                    "domain/planning/oracles/reading.py": AN_ORACLE.format(
                        name="ReadingOracle"
                    )
                },
            ),
            PORT_TEST,
            selector,
        )
        in_usecases = run_doctrine(
            a_solution(
                tmp_path / "usecases",
                {
                    "domain/planning/story.py": A_FROZEN_ENTITY,
                    "usecases/reading.py": AN_ORACLE.format(name="ReadingOracle"),
                },
            ),
            PORT_TEST,
            selector,
        )

        assert_doctrine_ran(in_an_area, 1, selector)
        assert in_an_area.returncode == 0, (
            "doctrine objected to an oracle declared in an area's oracles/:\n"
            + in_an_area.stdout
        )
        assert_doctrine_ran(in_usecases, 1, selector)
        assert in_usecases.returncode != 0, (
            "doctrine stopped objecting to an oracle declared in usecases/:\n"
            + in_usecases.stdout
        )


class TestAMisspeltKindDirectory:
    def test_a_port_in_one_is_objected_to_as_an_entity(self, tmp_path: Path) -> None:
        """domain/repositorys/ is an area, since no kind is spelt that
        way. A protocol in it is read as an entity, and is not one."""
        selector = "MUST_be_frozen_dataclasses"

        result = run_doctrine(
            a_solution(
                tmp_path,
                {
                    "domain/planning/story.py": A_FROZEN_ENTITY,
                    "domain/repositorys/story.py": A_REPOSITORY.format(
                        returns="Story | None"
                    ),
                },
            ),
            ENTITY_TEST,
            selector,
        )

        assert_doctrine_ran(result, 1, selector)
        assert result.returncode != 0, (
            "doctrine read a misspelt port directory and objected to "
            "nothing in it:\n" + result.stdout
        )
        assert "StoryRepository" in result.stdout
