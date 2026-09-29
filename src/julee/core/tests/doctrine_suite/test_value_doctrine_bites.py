"""What doctrine does with domain/values/, run against real solutions.

A value object has no identity, so no port is bound to one (ADR 018).
Doctrine reads that off the directory.

Both directions are checked, and the second matters more. A value read
as an entity is noisy: a port that names one is reported as bound to an
aggregate it has not got, and somebody goes and looks. An entity read as
a value is **silent** — the rules simply count one fewer thing and
object to less — so the test that an entity in domain/models/ is still
an entity is the one standing between this and a quiet hole.
"""

from pathlib import Path

import pytest

from .harness import a_julee_solution, assert_doctrine_ran, run_doctrine

pytestmark = pytest.mark.unit

PORT_TEST = "src/julee/core/doctrine/test_driven_port.py"
BINDING_SELECTOR = "name_no_entity"
EXPECTED_BINDING_TESTS = 1
"""The rule under test: what an oracle or witness may not be bound to.

The sibling rule about services is not selected, because a solution
with no services skips it, and a skipped rule is not a rule that
agreed."""

ENTITY = '''"""A story, which is kept under an id."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    """A unit of work."""

    slug: str
'''

VALUE = '''"""A score, which is nothing but what it holds."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Score:
    """How well something did. Two equal scores are one score."""

    points: int
'''

AN_ORACLE_NAMING = '''"""An oracle, which must be bound to no entity."""

from typing import Protocol, runtime_checkable

from acme.stories.domain.{package}.{module} import {name}


@runtime_checkable
class ReadingOracle(Protocol):
    """Fetches something from outside."""

    async def fetch(self, url: str) -> {name}: ...
'''


def a_solution_with(root: Path, named_by_the_oracle: str) -> Path:
    """Write a solution whose oracle returns one named class.

    Both a Story (an entity, in domain/models/) and a Score (a value, in
    domain/values/) are always written, so the two cases differ only in
    what the oracle names.

    Args:
        root: The solution root to write into
        named_by_the_oracle: "Story" or "Score"

    Returns:
        The root, ready to pass as JULEE_TARGET
    """
    context = a_julee_solution(root)
    for package in ("models", "values", "oracles"):
        (context / "domain" / package).mkdir(parents=True)
        (context / "domain" / package / "__init__.py").write_text("")
    (context / "domain" / "__init__.py").write_text("")
    (context / "usecases").mkdir()
    (context / "usecases" / "__init__.py").write_text("")

    (context / "domain" / "models" / "story.py").write_text(ENTITY)
    (context / "domain" / "values" / "score.py").write_text(VALUE)

    where = {"Story": ("models", "story"), "Score": ("values", "score")}
    package, module = where[named_by_the_oracle]
    (context / "domain" / "oracles" / "reading.py").write_text(
        AN_ORACLE_NAMING.format(
            package=package, module=module, name=named_by_the_oracle
        )
    )
    return root


def test_an_oracle_may_name_a_value(tmp_path: Path) -> None:
    """A value is not an aggregate, so naming one binds the oracle to
    nothing.

    This is what ceap's SchemaOracle was reported for: it returns a
    JsonSchema, which has no identity and which no repository keeps, and
    doctrine read it as an oracle bound to an entity because of the
    directory the class sat in.
    """
    result = run_doctrine(
        a_solution_with(tmp_path / "names-a-value", "Score"),
        PORT_TEST,
        BINDING_SELECTOR,
    )

    assert_doctrine_ran(result, EXPECTED_BINDING_TESTS, BINDING_SELECTOR)
    assert result.returncode == 0, (
        "doctrine objected to an oracle naming a value object:\n" + result.stdout
    )


def test_an_oracle_may_not_name_an_entity(tmp_path: Path) -> None:
    """The direction that fails quietly if this is wrong.

    An entity read as a value would make this pass, and nothing else
    would notice: the rules would count one fewer aggregate and object
    to less. So the same oracle is written twice, differing only in
    which class it returns, and this half must still be refused.
    """
    result = run_doctrine(
        a_solution_with(tmp_path / "names-an-entity", "Story"),
        PORT_TEST,
        BINDING_SELECTOR,
    )

    assert_doctrine_ran(result, EXPECTED_BINDING_TESTS, BINDING_SELECTOR)
    assert result.returncode != 0, (
        "doctrine stopped objecting to an oracle bound to an entity:\n" + result.stdout
    )
    assert "Story" in result.stdout, (
        "doctrine objected, but did not say which class:\n" + result.stdout
    )


def test_the_values_directory_is_not_objected_to(tmp_path: Path) -> None:
    """domain/values/ is a package doctrine reads, not an intruder.

    READ_DOMAIN_PACKAGES is derived from the layer paths, so this holds
    by construction — and would stop holding the moment someone spelled
    the package name twice instead of deriving it.
    """
    result = run_doctrine(
        a_solution_with(tmp_path / "package-is-known", "Score"),
        "src/julee/core/doctrine/test_entity.py",
        "package_under_domain",
    )

    assert result.returncode == 0, (
        "doctrine objected to domain/values/ as a package it does not "
        "read:\n" + result.stdout
    )
