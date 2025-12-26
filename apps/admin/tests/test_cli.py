"""Tests for julee-admin CLI.

These tests ensure the CLI commands are properly configured and don't fail
due to misconfiguration (missing paths, bad imports, etc.).

Test categories:
1. Configuration validity - paths and modules exist
2. Command smoke tests - commands run without crashing
3. Help text - all commands have working --help
"""

import importlib

import pytest
from click.testing import CliRunner

from apps.admin.cli import cli


class TestConfigurationValidity:
    """Test that configured paths and modules exist."""

    def test_doctrine_dir_exists(self) -> None:
        """DOCTRINE_DIR must point to an existing directory."""
        from apps.admin.commands.doctrine import DOCTRINE_DIR

        assert DOCTRINE_DIR.exists(), f"DOCTRINE_DIR does not exist: {DOCTRINE_DIR}"
        assert DOCTRINE_DIR.is_dir(), f"DOCTRINE_DIR is not a directory: {DOCTRINE_DIR}"

    def test_models_dir_exists(self) -> None:
        """MODELS_DIR must point to an existing directory."""
        from apps.admin.commands.doctrine import MODELS_DIR

        assert MODELS_DIR.exists(), f"MODELS_DIR does not exist: {MODELS_DIR}"
        assert MODELS_DIR.is_dir(), f"MODELS_DIR is not a directory: {MODELS_DIR}"

    def test_templates_dir_exists(self) -> None:
        """Templates directory must exist."""
        from apps.admin.commands.contexts import TEMPLATES_DIR

        assert TEMPLATES_DIR.exists(), f"TEMPLATES_DIR does not exist: {TEMPLATES_DIR}"
        assert TEMPLATES_DIR.is_dir(), f"TEMPLATES_DIR is not a directory: {TEMPLATES_DIR}"

    def test_doctrine_dir_has_test_files(self) -> None:
        """DOCTRINE_DIR must contain test files."""
        from apps.admin.commands.doctrine import DOCTRINE_DIR

        test_files = list(DOCTRINE_DIR.glob("test_*.py"))
        assert len(test_files) > 0, f"No test files in DOCTRINE_DIR: {DOCTRINE_DIR}"


class TestCommandImports:
    """Test that all command modules import without errors."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "apps.admin.cli",
            "apps.admin.commands.doctrine",
            "apps.admin.commands.contexts",
            "apps.admin.commands.routes",
            "apps.admin.commands.artifacts",
        ],
    )
    def test_module_imports(self, module_name: str) -> None:
        """All command modules must import without errors."""
        module = importlib.import_module(module_name)
        assert module is not None


class TestCommandHelp:
    """Test that all commands have working --help."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    def test_main_help(self, runner: CliRunner) -> None:
        """Main CLI --help must work."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Julee administration CLI" in result.output

    @pytest.mark.parametrize(
        "command",
        [
            ["doctrine", "--help"],
            ["doctrine", "list", "--help"],
            ["doctrine", "show", "--help"],
            ["doctrine", "verify", "--help"],
            ["contexts", "--help"],
            ["contexts", "list", "--help"],
            ["contexts", "show", "--help"],
            ["routes", "--help"],
            ["routes", "list", "--help"],
            ["routes", "show", "--help"],
            ["entities", "--help"],
            ["use-cases", "--help"],
            ["repositories", "--help"],
            ["services", "--help"],
            ["requests", "--help"],
            ["responses", "--help"],
        ],
    )
    def test_command_help(self, runner: CliRunner, command: list[str]) -> None:
        """All command --help must work without errors."""
        result = runner.invoke(cli, command)
        assert result.exit_code == 0, f"Command {command} failed: {result.output}"


class TestCommandExecution:
    """Test that commands execute without crashing on safe inputs."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    def test_doctrine_list(self, runner: CliRunner) -> None:
        """doctrine list must return doctrine areas."""
        result = runner.invoke(cli, ["doctrine", "list"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Core Doctrine:" in result.output

    def test_doctrine_show(self, runner: CliRunner) -> None:
        """doctrine show must display rules."""
        result = runner.invoke(cli, ["doctrine", "show"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "ARCHITECTURAL DOCTRINE" in result.output

    def test_doctrine_show_with_area_filter(self, runner: CliRunner) -> None:
        """doctrine show --area must filter results."""
        result = runner.invoke(cli, ["doctrine", "show", "--area", "pipeline"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Pipeline" in result.output

    def test_doctrine_show_invalid_area(self, runner: CliRunner) -> None:
        """doctrine show with invalid --area must fail gracefully."""
        result = runner.invoke(cli, ["doctrine", "show", "--area", "nonexistent"])
        assert result.exit_code == 1
        assert "No doctrine found" in result.output

    def test_contexts_list(self, runner: CliRunner) -> None:
        """contexts list must return bounded contexts."""
        result = runner.invoke(cli, ["contexts", "list"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        # Should find at least one context
        assert "hcd" in result.output or "c4" in result.output or "No bounded contexts" in result.output

    def test_contexts_show_nonexistent(self, runner: CliRunner) -> None:
        """contexts show with nonexistent slug must fail gracefully."""
        result = runner.invoke(cli, ["contexts", "show", "nonexistent-context"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_routes_list(self, runner: CliRunner) -> None:
        """routes list must not crash."""
        result = runner.invoke(cli, ["routes", "list"])
        assert result.exit_code == 0, f"Failed: {result.output}"


class TestDoctrineContent:
    """Test doctrine content is correctly extracted."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    def test_doctrine_has_expected_areas(self, runner: CliRunner) -> None:
        """Doctrine must include core architectural concepts."""
        result = runner.invoke(cli, ["doctrine", "list"])
        assert result.exit_code == 0

        # These are fundamental architectural concepts that should always exist
        expected_areas = ["Pipeline", "Use Case", "Entity"]
        for area in expected_areas:
            assert area in result.output, f"Missing expected doctrine area: {area}"

    def test_doctrine_rules_have_content(self, runner: CliRunner) -> None:
        """Doctrine rules must have actual content."""
        result = runner.invoke(cli, ["doctrine", "show"])
        assert result.exit_code == 0

        # Rules section should have actual rules (lines starting with "  - ")
        lines = result.output.split("\n")
        rule_lines = [line for line in lines if line.strip().startswith("- ")]
        assert len(rule_lines) > 0, "No rules found in doctrine output"
