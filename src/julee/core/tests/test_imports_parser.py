"""Tests for reading what a file imports."""

from pathlib import Path

import pytest

from julee.core.parsers.imports import extract_imports, imports_under

pytestmark = pytest.mark.unit


def a_file(tmp_path: Path, source: str, name: str = "thing.py") -> Path:
    """A Python file containing this source."""
    path = tmp_path / name
    path.write_text(source)
    return path


def test_a_plain_import_is_found(tmp_path: Path) -> None:
    """import x."""
    found = extract_imports(a_file(tmp_path, "import julee_hcd\n"))

    assert [info.module for info in found] == ["julee_hcd"]


def test_a_from_import_keeps_the_names_taken(tmp_path: Path) -> None:
    """Which name was taken can matter to a rule, so it is recorded."""
    found = extract_imports(
        a_file(tmp_path, "from julee_hcd.domain.models import Story, Epic\n")
    )

    assert found[0].module == "julee_hcd.domain.models"
    assert found[0].names == ("Story", "Epic")


def test_several_names_on_one_import_are_one_import(tmp_path: Path) -> None:
    """It is one statement and one place to fix."""
    found = extract_imports(a_file(tmp_path, "from a import b, c, d\n"))

    assert len(found) == 1


def test_several_modules_on_one_line_are_several_imports(tmp_path: Path) -> None:
    """Unlike the above: each names a different module."""
    found = extract_imports(a_file(tmp_path, "import a, b\n"))

    assert [info.module for info in found] == ["a", "b"]


def test_a_relative_import_says_so(tmp_path: Path) -> None:
    """A rule about reaching across packages should not trip on one."""
    found = extract_imports(a_file(tmp_path, "from .models import Story\n"))

    assert found[0].is_relative is True


def test_an_import_inside_a_function_is_found(tmp_path: Path) -> None:
    """The case the archived parser missed, and the one that hides things.

    Deferring an import is how a file reaches somewhere it should not,
    often to break a cycle and without meaning anything by it.
    """
    source = "def f():\n    from julee_c4.domain.models import Container\n    return Container\n"

    found = extract_imports(a_file(tmp_path, source))

    assert [info.module for info in found] == ["julee_c4.domain.models"]


def test_an_import_inside_a_class_is_found(tmp_path: Path) -> None:
    """Same reasoning, one level in."""
    source = "class A:\n    import julee_hcd\n"

    assert extract_imports(a_file(tmp_path, source))


def test_an_import_inside_a_try_is_found(tmp_path: Path) -> None:
    """An optional dependency is still an import."""
    source = "try:\n    import griffe\nexcept ImportError:\n    griffe = None\n"

    assert [info.module for info in extract_imports(a_file(tmp_path, source))] == [
        "griffe"
    ]


def test_the_line_is_recorded_so_the_objection_can_point_at_it(
    tmp_path: Path,
) -> None:
    """Whoever fixes it should not have to search the file."""
    found = extract_imports(a_file(tmp_path, "x = 1\n\n\nimport julee_hcd\n"))

    assert found[0].line == 4


def test_a_file_that_will_not_parse_yields_nothing(tmp_path: Path) -> None:
    """A codebase with a syntax error has a more pressing problem."""
    assert extract_imports(a_file(tmp_path, "def (\n")) == []


def test_a_file_that_is_not_there_yields_nothing(tmp_path: Path) -> None:
    """Rather than raising at whoever is walking a tree."""
    assert extract_imports(tmp_path / "absent.py") == []


def test_a_file_that_imports_nothing_yields_nothing(tmp_path: Path) -> None:
    """Most files do import something, but not all of them."""
    assert extract_imports(a_file(tmp_path, "x = 1\n")) == []


def test_every_file_under_a_directory_is_read(tmp_path: Path) -> None:
    """Which is how a rule sees a whole solution."""
    (tmp_path / "pkg").mkdir()
    a_file(tmp_path, "import a\n")
    a_file(tmp_path / "pkg", "import b\n", name="deep.py")

    assert {info.module for info in imports_under(tmp_path)} == {"a", "b"}


def test_a_virtualenv_is_not_read(tmp_path: Path) -> None:
    """Otherwise a rule reports on every dependency a solution has."""
    (tmp_path / ".venv").mkdir()
    a_file(tmp_path / ".venv", "import somebody_elses_problem\n", name="dep.py")
    a_file(tmp_path, "import a\n")

    assert [info.module for info in imports_under(tmp_path)] == ["a"]
