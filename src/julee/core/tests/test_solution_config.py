"""Tests for reading [tool.julee] out of a solution's pyproject.

Composition roots are the reason this file exists: the boundary rule
takes its carve-out from them, so a solution that declares none, or
declares them wrongly, changes what doctrine permits.
"""

from pathlib import Path

import pytest

from julee.core.infrastructure.repositories.file.solution_config import (
    FileSolutionConfigRepository,
)

pytestmark = pytest.mark.unit


def a_solution(root: Path, tool_julee: str = "") -> Path:
    """A project whose pyproject carries this [tool.julee] body."""
    (root / "pyproject.toml").write_text(
        '[project]\nname = "acme"\nversion = "0"\n\n'
        f'[tool.julee]\nsearch_root = "src/acme"\n{tool_julee}'
    )
    return root


def config(root: Path):
    """Read the policy config for that project."""
    return FileSolutionConfigRepository().get_policy_config_sync(root)


def test_composition_roots_default_to_apps(tmp_path: Path) -> None:
    """A solution that has never heard of this keeps what it had."""
    assert config(a_solution(tmp_path)).composition_roots == ("apps",)


def test_a_solution_may_declare_its_own(tmp_path: Path) -> None:
    root = a_solution(
        tmp_path, 'composition_roots = ["sphinx_hcd/sphinx", "sphinx_c4/sphinx"]\n'
    )

    assert config(root).composition_roots == (
        "sphinx_hcd/sphinx",
        "sphinx_c4/sphinx",
    )


def test_declaring_roots_replaces_the_default_rather_than_adding_to_it(
    tmp_path: Path,
) -> None:
    """A solution saying where it wires things is saying where, not also."""
    root = a_solution(tmp_path, 'composition_roots = ["wiring"]\n')

    assert config(root).composition_roots == ("wiring",)


def test_an_empty_list_is_not_read_as_unset(tmp_path: Path) -> None:
    """Holding every file to what the kits offer is a thing to want,
    and must not silently come back as apps/."""
    root = a_solution(tmp_path, "composition_roots = []\n")

    assert config(root).composition_roots == ()


def test_a_project_without_tool_julee_is_not_a_solution(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "acme"\nversion = "0"\n'
    )

    assert config(tmp_path).is_julee_solution is False


def test_the_other_fields_still_read(tmp_path: Path) -> None:
    """Guards the new field against having displaced an old one."""
    root = a_solution(tmp_path, 'kits = ["hcd", "c4"]\ndocs_root = "docs"\n')
    found = config(root)

    assert found.search_root == "src/acme"
    assert found.docs_root == "docs"
    assert found.kits == ("hcd", "c4")
    assert found.is_julee_solution is True
