"""The facade rule, run against real solutions.

Both directions. A solution with a re-exporting ``__init__.py`` must be
objected to, and one whose ``__init__.py`` files hold docstrings alone
must not — the second is the one that fails quietly if the collector
walks the wrong root or skips the wrong directories, because a rule
that reads nothing objects to nothing.
"""

from pathlib import Path

import pytest

from .harness import a_julee_solution, assert_doctrine_ran, run_doctrine

pytestmark = pytest.mark.unit

FACADE_TEST = "src/julee/core/doctrine/test_facade.py"
SELECTOR = "re_export"
EXPECTED_TESTS = 1

STORY = '''"""The Story entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    """A unit of work."""

    slug: str
'''

FACADE = '''"""Models, re-exported for convenience."""

from .story import Story

__all__ = ["Story"]
'''


def a_solution(root: Path, models_init: str) -> Path:
    """Write a solution whose domain/models/__init__.py is as given.

    Args:
        root: The solution root to write into
        models_init: The text of domain/models/__init__.py

    Returns:
        The root, ready to pass as JULEE_TARGET
    """
    context = a_julee_solution(root)
    (context / "domain" / "models").mkdir(parents=True)
    (context / "domain" / "__init__.py").write_text('"""The domain."""\n')
    (context / "domain" / "models" / "__init__.py").write_text(models_init)
    (context / "domain" / "models" / "story.py").write_text(STORY)
    return root


def test_a_re_exporting_init_is_objected_to(tmp_path: Path) -> None:
    """The facade, named by file and by name."""
    result = run_doctrine(
        a_solution(tmp_path / "facade", FACADE), FACADE_TEST, SELECTOR
    )

    assert_doctrine_ran(result, EXPECTED_TESTS, SELECTOR)
    assert result.returncode != 0, "doctrine let a re-export through:\n" + result.stdout
    assert "domain/models/__init__.py re-exports Story" in result.stdout


def test_a_docstring_only_init_is_not(tmp_path: Path) -> None:
    """The direction that fails quietly if the collector is wrong."""
    result = run_doctrine(
        a_solution(tmp_path / "bare", '"""Models."""\n'), FACADE_TEST, SELECTOR
    )

    assert_doctrine_ran(result, EXPECTED_TESTS, SELECTOR)
    assert result.returncode == 0, (
        "doctrine objected to an __init__.py holding a docstring alone:\n"
        + result.stdout
    )
