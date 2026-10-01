"""What doctrine does with a file it cannot read, run against real solutions.

The parser returns the classes of the files it could read. A file that
does not parse gives it none, and until this rule a run over a solution
holding such a file passed with the totals it would have had without it.

The case that matters is a file nothing imports. Once something imports
a broken module the rules that import say so; before that, nothing does.
"""

from pathlib import Path

import pytest

from .harness import a_julee_solution, assert_doctrine_ran, run_doctrine

pytestmark = pytest.mark.unit

DISCOVERY_TEST = "src/julee/core/doctrine/test_discovery.py"
READING_SELECTOR = "be_readable"
EXPECTED_READING_TESTS = 1

ENTITY = '''"""A story, which is kept under an id."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    """A unit of work."""

    slug: str
'''

A_VALUE_THAT_DOES_NOT_PARSE = '''"""A score, half written."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Score:
    """How well something did."""

    points: int


def broken(:
'''


def a_solution(root: Path) -> Path:
    """Write a solution with one entity and nothing that imports it.

    Args:
        root: The solution root to write into

    Returns:
        The bounded context directory, for the caller to add to
    """
    context = a_julee_solution(root)
    for package in ("models", "values"):
        (context / "domain" / package).mkdir(parents=True)
        (context / "domain" / package / "__init__.py").write_text("")
    (context / "domain" / "__init__.py").write_text("")
    (context / "domain" / "models" / "story.py").write_text(ENTITY)
    return context


def test_a_solution_that_parses_is_not_objected_to(tmp_path: Path) -> None:
    root = tmp_path / "parses"
    a_solution(root)

    result = run_doctrine(root, DISCOVERY_TEST, READING_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_READING_TESTS, READING_SELECTOR)
    assert result.returncode == 0, (
        "doctrine objected to a solution it could read:\n" + result.stdout
    )


def test_a_file_that_does_not_parse_is_objected_to(tmp_path: Path) -> None:
    """The direction that was silent.

    Nothing imports the value, so no rule that imports can notice it,
    and every rule that reads classes sees a context with one fewer.
    """
    root = tmp_path / "does-not-parse"
    context = a_solution(root)
    (context / "domain" / "values" / "score.py").write_text(A_VALUE_THAT_DOES_NOT_PARSE)

    result = run_doctrine(root, DISCOVERY_TEST, READING_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_READING_TESTS, READING_SELECTOR)
    assert result.returncode != 0, (
        "doctrine passed over a file it could not read:\n" + result.stdout
    )
    assert "src/acme/stories/domain/values/score.py" in result.stdout, (
        "doctrine objected, but did not say which file:\n" + result.stdout
    )
    assert "line 13" in result.stdout, (
        "doctrine objected, but did not say where it stopped:\n" + result.stdout
    )


def test_a_test_file_that_does_not_parse_is_not_objected_to(tmp_path: Path) -> None:
    """Doctrine does not read a context's tests, so it does not ask them to parse.

    The rule is about files doctrine went to read. Widening it to every
    file in the tree would make doctrine object to code it has never had
    an opinion about.
    """
    root = tmp_path / "broken-test"
    context = a_solution(root)
    (context / "tests").mkdir()
    (context / "tests" / "test_score.py").write_text(A_VALUE_THAT_DOES_NOT_PARSE)

    result = run_doctrine(root, DISCOVERY_TEST, READING_SELECTOR)

    assert_doctrine_ran(result, EXPECTED_READING_TESTS, READING_SELECTOR)
    assert result.returncode == 0, (
        "doctrine objected to a file it does not read:\n" + result.stdout
    )
