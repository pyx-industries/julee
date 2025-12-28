"""Compliance tests for Test Organization policy.

These tests verify that a solution organizes tests consistently.
"""

from pathlib import Path

import pytest

from julee.core.doctrine_constants import (
    SEARCH_ROOT,
    TEST_CONFTEST,
    TEST_FILE_PATTERN,
    TEST_INIT,
    TEST_MARKERS,
    TESTS_ROOT,
)
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)


class TestBoundedContextTestStructure:
    """Compliance tests for test organization within bounded contexts."""

    @pytest.mark.asyncio
    async def test_every_bounded_context_MUST_have_tests_directory(
        self, repo: FilesystemBoundedContextRepository
    ):
        """Every bounded context MUST have a tests/ subdirectory.

        Tests are essential for maintaining code quality and documenting
        expected behavior. A bounded context without tests is incomplete.
        """
        contexts = await repo.list_all()

        missing_tests = []
        for ctx in contexts:
            tests_path = Path(ctx.path) / TESTS_ROOT
            if not tests_path.is_dir():
                missing_tests.append(ctx.slug)

        assert (
            not missing_tests
        ), f"Bounded contexts missing {TESTS_ROOT}/: {missing_tests}"

    @pytest.mark.asyncio
    async def test_tests_directory_MUST_have_init_py(
        self, repo: FilesystemBoundedContextRepository
    ):
        """The tests/ directory MUST have __init__.py for proper imports.

        Without __init__.py, pytest may have issues with imports and
        the test directory won't be a proper Python package.
        """
        contexts = await repo.list_all()

        missing_init = []
        for ctx in contexts:
            tests_path = Path(ctx.path) / TESTS_ROOT
            if tests_path.is_dir():
                init_path = tests_path / TEST_INIT
                if not init_path.exists():
                    missing_init.append(ctx.slug)

        assert (
            not missing_init
        ), f"Bounded contexts with tests/ missing {TEST_INIT}: {missing_init}"

    @pytest.mark.asyncio
    async def test_test_files_MUST_follow_naming_convention(
        self, repo: FilesystemBoundedContextRepository
    ):
        """Test files MUST be named test_*.py for pytest discoverability.

        Pytest discovers tests by looking for files matching the pattern
        test_*.py. Files not following this convention won't be run.
        """
        contexts = await repo.list_all()

        non_compliant = []
        for ctx in contexts:
            tests_path = Path(ctx.path) / TESTS_ROOT
            if tests_path.is_dir():
                for py_file in tests_path.rglob("*.py"):
                    if py_file.name == "__init__.py":
                        continue
                    if py_file.name == TEST_CONFTEST:
                        continue
                    if py_file.name == "factories.py":
                        # Test factories are allowed
                        continue
                    if not py_file.name.startswith("test_"):
                        non_compliant.append(f"{ctx.slug}: {py_file.name}")

        assert (
            not non_compliant
        ), f"Test files not following {TEST_FILE_PATTERN}: {non_compliant}"


class TestSolutionTestConfiguration:
    """Compliance tests for pytest configuration at solution level."""

    def test_solution_MUST_have_pyproject_toml(self, project_root: Path):
        """Every solution MUST have a pyproject.toml file.

        The pyproject.toml provides centralized configuration for pytest
        and other development tools.
        """
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "Solution MUST have pyproject.toml"

    def test_pyproject_MUST_configure_pytest(self, project_root: Path):
        """The pyproject.toml MUST include pytest configuration.

        Pytest configuration ensures consistent test discovery and
        execution across the solution.
        """
        pyproject = project_root / "pyproject.toml"

        content = pyproject.read_text()
        assert (
            "[tool.pytest.ini_options]" in content
        ), "pyproject.toml MUST have [tool.pytest.ini_options] section"

    def test_pytest_config_MUST_specify_testpaths(self, project_root: Path):
        """Pytest configuration MUST specify testpaths for discoverability.

        The testpaths setting tells pytest where to look for tests,
        ensuring all bounded context tests are discovered.
        """
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()

        assert "testpaths" in content, "pytest config MUST specify testpaths"
        assert SEARCH_ROOT in content, f"testpaths MUST include '{SEARCH_ROOT}'"

    def test_pytest_config_MUST_define_standard_markers(self, project_root: Path):
        """Pytest configuration MUST define standard test markers.

        Markers allow classification of tests (unit, integration, e2e)
        for selective test execution.
        """
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()

        assert "markers" in content, "pytest config MUST define markers"

        for marker in TEST_MARKERS:
            assert marker in content, f"pytest config MUST define '{marker}' marker"

    def test_integration_tests_MUST_be_excluded_by_default(self, project_root: Path):
        """Integration tests MUST be excluded from default test runs.

        Integration tests are slower and require external dependencies.
        They should only run when explicitly requested.
        """
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()

        assert (
            "not integration" in content
        ), "pytest addopts MUST exclude integration tests by default"
