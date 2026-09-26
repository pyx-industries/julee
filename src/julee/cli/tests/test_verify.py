"""Tests for what `julee doctrine verify` decides before it runs anything."""

from pathlib import Path

import pytest

from julee.cli.verify import (
    claim_packages_in,
    enclosing_solution,
    packages_doctrine_cannot_import,
    pytest_arguments,
    resolve_target,
    target_objections,
)
from julee.core.entities.policy import SolutionPolicyConfig

pytestmark = pytest.mark.unit


@pytest.fixture
def solution(tmp_path: Path) -> Path:
    """A minimal julee solution: a declaration and somewhere to look."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "acme"\n\n[tool.julee]\nsearch_root = "src"\n'
    )
    (tmp_path / "src").mkdir()
    return tmp_path


def a_config(**overrides: object) -> SolutionPolicyConfig:
    return SolutionPolicyConfig(
        **{"is_julee_solution": True, "search_root": "src", **overrides}  # type: ignore[arg-type]
    )


# =============================================================================
# Which codebase gets checked
# =============================================================================


class TestResolvingTheTarget:
    def test_an_explicit_target_wins(self, tmp_path: Path) -> None:
        assert resolve_target(str(tmp_path), Path("/elsewhere")) == tmp_path

    def test_the_working_directory_is_the_default(self, solution: Path) -> None:
        """#192: it used to be whichever checkout contained julee itself."""
        assert resolve_target(None, solution) == solution

    def test_a_subdirectory_resolves_to_the_solution_above_it(
        self, solution: Path
    ) -> None:
        """Running from src/ or tests/ should mean the obvious thing."""
        assert resolve_target(None, solution / "src") == solution

    def test_somewhere_that_is_no_solution_stays_put(self, tmp_path: Path) -> None:
        """So the objection names where the operator actually is."""
        assert resolve_target(None, tmp_path) == tmp_path

    def test_a_user_path_is_expanded(self) -> None:
        assert not str(resolve_target("~/acme", Path.cwd())).startswith("~")


class TestFindingTheEnclosingSolution:
    def test_the_directory_itself_counts(self, solution: Path) -> None:
        assert enclosing_solution(solution) == solution

    def test_the_nearest_one_wins(self, solution: Path) -> None:
        """A kit inside a workspace is its own solution."""
        inner = solution / "kits" / "billing"
        inner.mkdir(parents=True)
        (inner / "pyproject.toml").write_text('[tool.julee]\nsearch_root = "src"\n')

        assert enclosing_solution(inner) == inner

    def test_a_pyproject_without_the_section_is_not_one(self, tmp_path: Path) -> None:
        """Every Python project has a pyproject; not every one is a solution."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "plain"\n')

        assert enclosing_solution(tmp_path) is None

    def test_nothing_above_means_nothing(self, tmp_path: Path) -> None:
        assert enclosing_solution(tmp_path) is None

    def test_an_unreadable_pyproject_does_not_stop_the_search(
        self, solution: Path
    ) -> None:
        """A broken file higher up should not hide a good one below."""
        inner = solution / "inner"
        inner.mkdir()
        (inner / "pyproject.toml").write_bytes(b"\xff\xfe not text at all")

        assert enclosing_solution(inner) == solution


# =============================================================================
# Whether the question can be asked at all
# =============================================================================


class TestWhetherItCanRun:
    def test_a_solution_raises_no_objection(self, solution: Path) -> None:
        assert target_objections(solution, a_config()) == []

    def test_a_missing_directory_is_objected_to(self, tmp_path: Path) -> None:
        assert target_objections(tmp_path / "nope", a_config())

    def test_a_directory_with_no_pyproject_is_objected_to(self, tmp_path: Path) -> None:
        assert target_objections(tmp_path, a_config())

    def test_a_project_that_is_not_a_solution_is_objected_to(
        self, solution: Path
    ) -> None:
        """Running anyway would report green about nothing."""
        (objection,) = target_objections(
            solution, a_config(is_julee_solution=False, search_root=None)
        )

        assert "[tool.julee]" in objection

    def test_a_solution_with_no_search_root_is_objected_to(
        self, solution: Path
    ) -> None:
        (objection,) = target_objections(solution, a_config(search_root=None))

        assert "search_root" in objection

    def test_a_search_root_pointing_nowhere_is_objected_to(
        self, solution: Path
    ) -> None:
        """The typo that #240 is about, caught before the run rather than
        reported as a clean sheet."""
        (objection,) = target_objections(solution, a_config(search_root="srcc"))

        assert "srcc" in objection


# =============================================================================
# The premise the semantics rules rest on (#269)
# =============================================================================


class TestTheImportPremise:
    def test_claim_publishers_are_found_by_their_directory(
        self, solution: Path
    ) -> None:
        package = solution / "src" / "acme"
        package.mkdir(parents=True)
        (package / "semantics.toml").write_text("")

        assert claim_packages_in(solution) == ["acme"]

    def test_an_installed_kits_claims_are_not_the_solutions_problem(
        self, solution: Path
    ) -> None:
        """A .venv holds every dependency's semantics.toml."""
        vendored = solution / ".venv" / "lib" / "julee_hcd"
        vendored.mkdir(parents=True)
        (vendored / "semantics.toml").write_text("")

        assert claim_packages_in(solution) == []

    def test_an_importable_publisher_raises_no_objection(self) -> None:
        assert packages_doctrine_cannot_import(["acme"], lambda _: True) == []

    def test_a_publisher_that_is_not_installed_is_objected_to(self) -> None:
        """#269: every claim it makes would read as naming a missing class."""
        (objection,) = packages_doctrine_cannot_import(["acme"], lambda _: False)

        assert "acme" in objection
        assert "not importable" in objection

    def test_a_target_publishing_nothing_has_no_premise_to_check(self) -> None:
        assert packages_doctrine_cannot_import([], lambda _: False) == []


# =============================================================================
# How doctrine gets run
# =============================================================================


class TestHowDoctrineIsRun:
    def test_the_doctrine_package_is_what_gets_collected(self, tmp_path: Path) -> None:
        assert "julee.core.doctrine" in pytest_arguments(tmp_path)

    def test_the_targets_own_pytest_options_are_not_inherited(
        self, tmp_path: Path
    ) -> None:
        """Otherwise the result depends on the solution's test setup —
        its coverage settings, its plugins, its -x — rather than on its
        architecture."""
        arguments = pytest_arguments(tmp_path)

        assert "addopts=" in arguments
