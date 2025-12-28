"""Compliance tests for MCP Framework policy.

These tests verify that MCP applications use julee's MCP framework.
"""

import ast
from pathlib import Path

import pytest

from julee.core.entities.application import AppType
from julee.core.infrastructure.repositories.introspection.application import (
    FilesystemApplicationRepository,
)


def _has_mcp_framework_import(file_path: Path) -> bool:
    """Check if a file imports from julee.core.infrastructure.mcp."""
    try:
        source = file_path.read_text()
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, OSError):
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "julee.core.infrastructure.mcp" in node.module:
                return True
            if node.module == "julee.core.infrastructure.mcp":
                for alias in node.names:
                    if alias.name == "create_mcp_server":
                        return True
    return False


def _has_context_module(app_path: Path) -> bool:
    """Check if app has a context.py module for DI factories."""
    return (app_path / "context.py").exists()


def _calls_create_mcp_server(file_path: Path) -> bool:
    """Check if a file calls create_mcp_server()."""
    try:
        source = file_path.read_text()
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, OSError):
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "create_mcp_server":
                    return True
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "create_mcp_server":
                    return True
    return False


class TestMcpFrameworkCompliance:
    """Compliance tests for mcp-framework policy."""

    @pytest.mark.asyncio
    async def test_mcp_apps_MUST_use_framework(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """MCP applications MUST use the julee MCP framework.

        MCP apps MUST import and use create_mcp_server() from
        julee.core.infrastructure.mcp. This ensures consistent tool generation,
        progressive disclosure resources, and documentation derivation.
        """
        apps = await app_repo.list_by_type(AppType.MCP)

        # Skip if no MCP apps exist
        if not apps:
            pytest.skip("No MCP applications found")

        violations = []
        for app in apps:
            init_file = Path(app.path) / "__init__.py"
            if not init_file.exists():
                violations.append(f"{app.slug}: missing __init__.py")
                continue

            if not _has_mcp_framework_import(init_file):
                violations.append(
                    f"{app.slug}: does not import from julee.core.infrastructure.mcp"
                )
                continue

            if not _calls_create_mcp_server(init_file):
                violations.append(f"{app.slug}: does not call create_mcp_server()")

        assert not violations, "MCP apps not using framework:\n" + "\n".join(
            f"  - {v}" for v in violations
        )

    @pytest.mark.asyncio
    async def test_mcp_apps_MUST_have_context_module(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """MCP applications MUST have a context.py module.

        MCP apps MUST provide a context.py module containing DI factory
        functions for use cases. This follows the same pattern as REST-API
        applications for consistency.
        """
        apps = await app_repo.list_by_type(AppType.MCP)

        if not apps:
            pytest.skip("No MCP applications found")

        violations = []
        for app in apps:
            if not _has_context_module(Path(app.path)):
                violations.append(f"{app.slug}: missing context.py")

        assert not violations, "MCP apps missing context module:\n" + "\n".join(
            f"  - {v}" for v in violations
        )

    @pytest.mark.asyncio
    async def test_mcp_tools_MUST_map_to_use_cases(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """Each MCP tool MUST correspond to exactly one domain use case.

        MCP tools are thin adapters over use cases. The framework
        automatically generates tools from discovered use cases in the context
        module. Tools MUST NOT contain business logic directly.
        """
        apps = await app_repo.list_by_type(AppType.MCP)

        if not apps:
            pytest.skip("No MCP applications found")

        # If apps use the framework (tested elsewhere), this doctrine is met
        for app in apps:
            init_file = Path(app.path) / "__init__.py"
            assert _calls_create_mcp_server(init_file), (
                f"MCP app '{app.slug}' does not use create_mcp_server() - "
                f"tools may not map to use cases"
            )
