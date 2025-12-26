"""Admin CLI app instance doctrine.

These tests ARE the doctrine for the admin CLI application.
The docstrings are doctrine statements. The assertions enforce them.

This is App Instance Doctrine - rules specific to the admin app.
It supplements Core Doctrine and CLI App Type Doctrine.

Doctrine:
- Admin CLI MUST expose commands for all discoverable core entities
- Admin CLI MUST provide list operations for solution structure entities
- Admin CLI MUST provide doctrine verification commands
"""

import ast
from pathlib import Path

import pytest

# Core entities that represent solution structure - these should be inspectable
SOLUTION_STRUCTURE_ENTITIES: frozenset[str] = frozenset(
    {
        "Solution",
        "BoundedContext",
        "Application",
        "Deployment",
    }
)

# BC artifact types - already covered via artifact commands
BC_ARTIFACT_TYPES: frozenset[str] = frozenset(
    {
        "Entity",
        "UseCase",
        "Request",
        "Response",
        "Repository",
        "Service",
    }
)


def _extract_click_commands(file_path: Path) -> list[dict]:
    """Extract Click command definitions from a Python file using AST.

    Returns list of dicts with:
    - name: command function name
    - type: 'command' or 'group'
    - file: source file path
    - line: line number
    """
    try:
        source = file_path.read_text()
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return []

    commands = []
    click_decorators = {"command", "group"}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for decorator in node.decorator_list:
                decorator_name = None

                # Handle @click.command(), @click.group()
                if isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Attribute):
                        if decorator.func.attr in click_decorators:
                            decorator_name = decorator.func.attr
                    elif isinstance(decorator.func, ast.Name):
                        if decorator.func.id in click_decorators:
                            decorator_name = decorator.func.id

                # Handle @group.command(), @cli.command()
                elif isinstance(decorator, ast.Attribute):
                    if decorator.attr in click_decorators:
                        decorator_name = decorator.attr

                if decorator_name:
                    commands.append(
                        {
                            "name": node.name,
                            "type": decorator_name,
                            "file": str(file_path),
                            "line": node.lineno,
                        }
                    )
                    break

    return commands


def _discover_admin_commands(admin_root: Path) -> list[dict]:
    """Discover all Click commands in the admin app."""
    commands_dir = admin_root / "commands"
    all_commands = []

    if commands_dir.exists():
        for py_file in commands_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            all_commands.extend(_extract_click_commands(py_file))

    # Also check cli.py
    cli_file = admin_root / "cli.py"
    if cli_file.exists():
        all_commands.extend(_extract_click_commands(cli_file))

    return all_commands


# =============================================================================
# DOCTRINE: Solution Structure Commands
# =============================================================================


class TestAdminSolutionStructureCommands:
    """Admin CLI MUST expose commands for solution structure entities."""

    def test_admin_MUST_have_contexts_command(self, admin_root: Path) -> None:
        """Admin CLI MUST have commands for listing bounded contexts.

        Bounded contexts are the fundamental organizational unit. Users need
        to discover and inspect them.
        """
        commands = _discover_admin_commands(admin_root)
        command_names = {cmd["name"].lower() for cmd in commands}

        has_contexts = any("context" in name for name in command_names)
        assert has_contexts, (
            "Admin CLI MUST have commands for bounded contexts. "
            f"Found commands: {sorted(command_names)}"
        )

    def test_admin_MUST_have_solution_command(self, admin_root: Path) -> None:
        """Admin CLI MUST have commands for the Solution entity.

        Users need to inspect the current solution structure, including
        its bounded contexts, applications, and deployments.
        """
        commands = _discover_admin_commands(admin_root)
        command_names = {cmd["name"].lower() for cmd in commands}

        has_solution = any("solution" in name for name in command_names)
        assert has_solution, (
            "Admin CLI MUST have commands for Solution entity. "
            f"Found commands: {sorted(command_names)}"
        )

    def test_admin_MUST_have_apps_command(self, admin_root: Path) -> None:
        """Admin CLI MUST have commands for listing applications.

        Users need to discover and inspect applications in the solution.
        """
        commands = _discover_admin_commands(admin_root)
        command_names = {cmd["name"].lower() for cmd in commands}

        has_apps = any("app" in name for name in command_names)
        assert has_apps, (
            "Admin CLI MUST have commands for Application entity. "
            f"Found commands: {sorted(command_names)}"
        )

    def test_admin_MUST_have_deployments_command(self, admin_root: Path) -> None:
        """Admin CLI MUST have commands for listing deployments.

        Users need to discover and inspect deployments in the solution.
        """
        commands = _discover_admin_commands(admin_root)
        command_names = {cmd["name"].lower() for cmd in commands}

        has_deployments = any("deploy" in name for name in command_names)
        assert has_deployments, (
            "Admin CLI MUST have commands for Deployment entity. "
            f"Found commands: {sorted(command_names)}"
        )


# =============================================================================
# DOCTRINE: BC Artifact Commands
# =============================================================================


class TestAdminBCArtifactCommands:
    """Admin CLI MUST expose commands for BC artifact introspection."""

    def test_admin_MUST_have_entities_command(self, admin_root: Path) -> None:
        """Admin CLI MUST have commands for listing entities across BCs."""
        commands = _discover_admin_commands(admin_root)
        command_names = {cmd["name"].lower() for cmd in commands}

        has_entities = any("entit" in name for name in command_names)
        assert has_entities, (
            "Admin CLI MUST have commands for listing entities. "
            f"Found commands: {sorted(command_names)}"
        )

    def test_admin_MUST_have_usecases_command(self, admin_root: Path) -> None:
        """Admin CLI MUST have commands for listing use cases across BCs."""
        commands = _discover_admin_commands(admin_root)
        command_names = {cmd["name"].lower() for cmd in commands}

        has_usecases = any("usecase" in name or "use_case" in name for name in command_names)
        assert has_usecases, (
            "Admin CLI MUST have commands for listing use cases. "
            f"Found commands: {sorted(command_names)}"
        )


# =============================================================================
# DOCTRINE: Doctrine Commands
# =============================================================================


class TestAdminDoctrineCommands:
    """Admin CLI MUST expose doctrine management commands."""

    def test_admin_MUST_have_doctrine_show_command(self, admin_root: Path) -> None:
        """Admin CLI MUST have a command to display doctrine rules."""
        commands = _discover_admin_commands(admin_root)
        command_names = {cmd["name"].lower() for cmd in commands}

        has_doctrine = any("doctrine" in name for name in command_names)
        assert has_doctrine, (
            "Admin CLI MUST have doctrine commands. "
            f"Found commands: {sorted(command_names)}"
        )

    def test_admin_MUST_have_doctrine_verify_command(self, admin_root: Path) -> None:
        """Admin CLI MUST have a command to verify doctrine compliance.

        Users need to be able to check their codebase against doctrine rules.
        """
        commands = _discover_admin_commands(admin_root)
        command_names = {cmd["name"].lower() for cmd in commands}

        # Look for verify in doctrine-related commands
        has_verify = any("verify" in name for name in command_names)
        assert has_verify, (
            "Admin CLI MUST have doctrine verify command. "
            f"Found commands: {sorted(command_names)}"
        )
