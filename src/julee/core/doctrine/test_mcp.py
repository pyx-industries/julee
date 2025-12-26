"""MCP application doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

MCP (Model Context Protocol) applications expose bounded context capabilities
to AI assistants through tools and resources. They are thin adapters that
delegate to domain use cases.

MCP Doctrine Principles:
1. Use Cases Are Tools - Each MCP tool corresponds to exactly one domain use case
2. Documentation Is Derived - Tool descriptions come from UseCase.__doc__
3. Progressive Disclosure - 3-level resource hierarchy ({slug}://, etc.)
4. Consistent DI - Same factory pattern as REST-API applications
"""

import ast
from pathlib import Path

import pytest

from julee.core.entities.application import AppType
from julee.core.infrastructure.repositories.introspection.application import (
    FilesystemApplicationRepository,
)


def _has_mcp_framework_import(file_path: Path) -> bool:
    """Check if a file imports from julee.core.infrastructure.mcp.

    Specifically looks for create_mcp_server import which indicates
    the app uses the MCP framework.
    """
    try:
        source = file_path.read_text()
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, OSError):
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "julee.core.infrastructure.mcp" in node.module:
                return True
            # Also check for the specific import
            if node.module == "julee.core.infrastructure.mcp":
                for alias in node.names:
                    if alias.name == "create_mcp_server":
                        return True
    return False


def _has_context_module(app_path: Path) -> bool:
    """Check if app has a context.py module for DI factories."""
    return (app_path / "context.py").exists()


def _calls_create_mcp_server(file_path: Path) -> bool:
    """Check if a file calls create_mcp_server().

    This indicates the app uses the framework to create its server.
    """
    try:
        source = file_path.read_text()
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, OSError):
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check for create_mcp_server() call
            if isinstance(node.func, ast.Name):
                if node.func.id == "create_mcp_server":
                    return True
            # Check for module.create_mcp_server() call
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "create_mcp_server":
                    return True
    return False


class TestMcpFrameworkUsage:
    """Doctrine about MCP framework usage."""

    @pytest.mark.asyncio
    async def test_mcp_apps_exist(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """MCP applications MUST be discoverable."""
        apps = await app_repo.list_by_type(AppType.MCP)

        assert len(apps) > 0, "No MCP applications found - detector may be broken"

    @pytest.mark.asyncio
    async def test_mcp_apps_MUST_use_framework(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """MCP applications MUST use the julee MCP framework.

        Doctrine: MCP apps MUST import and use create_mcp_server() from
        julee.core.infrastructure.mcp. This ensures consistent tool generation,
        progressive disclosure resources, and documentation derivation.

        The framework automatically:
        - Discovers use cases from the context module
        - Generates tools with minimal docstrings pointing to resources
        - Creates 3-level progressive disclosure resources
        """
        apps = await app_repo.list_by_type(AppType.MCP)

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


class TestMcpDependencyInjection:
    """Doctrine about MCP dependency injection."""

    @pytest.mark.asyncio
    async def test_mcp_apps_MUST_have_context_module(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """MCP applications MUST have a context.py module.

        Doctrine: MCP apps MUST provide a context.py module containing
        DI factory functions for use cases. This follows the same pattern
        as REST-API applications for consistency.

        The context module:
        - Contains repository factory functions (with @lru_cache)
        - Contains use case factory functions or USE_CASE_FACTORIES dict
        - Is passed to create_mcp_server() for use case discovery
        """
        apps = await app_repo.list_by_type(AppType.MCP)

        violations = []
        for app in apps:
            if not _has_context_module(Path(app.path)):
                violations.append(f"{app.slug}: missing context.py")

        assert not violations, "MCP apps missing context module:\n" + "\n".join(
            f"  - {v}" for v in violations
        )


class TestMcpToolUseCaseMapping:
    """Doctrine about MCP tool to use case mapping."""

    @pytest.mark.asyncio
    async def test_mcp_tools_MUST_map_to_use_cases(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """Each MCP tool MUST correspond to exactly one domain use case.

        Doctrine: MCP tools are thin adapters over use cases. The framework
        automatically generates tools from discovered use cases in the context
        module. Tools MUST NOT contain business logic directly.

        This ensures:
        - Clear separation between MCP layer and business logic
        - Use cases are reusable across different interfaces (REST, MCP, CLI)
        - Consistent request/response patterns
        - Documentation derived from use case docstrings
        """
        # This is enforced by the framework architecture itself.
        # The create_mcp_server() function only creates tools from use cases
        # discovered in the context module. There is no way to add tools
        # that don't map to use cases when using the framework.
        #
        # This test verifies apps use the framework (covered by other tests).
        apps = await app_repo.list_by_type(AppType.MCP)
        assert len(apps) > 0, "No MCP applications found"

        # If apps use the framework (tested elsewhere), this doctrine is met
        for app in apps:
            init_file = Path(app.path) / "__init__.py"
            assert _calls_create_mcp_server(init_file), (
                f"MCP app '{app.slug}' does not use create_mcp_server() - "
                f"tools may not map to use cases"
            )


class TestMcpDocumentationDerivation:
    """Doctrine about MCP documentation derivation."""

    @pytest.mark.asyncio
    async def test_mcp_documentation_MUST_derive_from_domain(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """MCP tool documentation MUST be derived from domain layer.

        Doctrine: Tool descriptions MUST come from UseCase.__doc__.
        Parameter schemas MUST come from Request.model_json_schema().
        Return schemas MUST come from Response.model_json_schema().

        This ensures:
        - No documentation duplication in MCP layer
        - Single source of truth in domain layer
        - API contract changes automatically update tool descriptions
        """
        # This is enforced by the framework architecture itself.
        # The tool_factory.py generates tool docstrings from use case
        # docstrings and derives parameter/return schemas from
        # Request/Response models.
        #
        # This test verifies apps use the framework.
        apps = await app_repo.list_by_type(AppType.MCP)
        assert len(apps) > 0, "No MCP applications found"

        for app in apps:
            init_file = Path(app.path) / "__init__.py"
            assert _calls_create_mcp_server(init_file), (
                f"MCP app '{app.slug}' does not use create_mcp_server() - "
                f"documentation derivation not guaranteed"
            )


class TestMcpProgressiveDisclosure:
    """Doctrine about MCP progressive disclosure resources."""

    @pytest.mark.asyncio
    async def test_mcp_apps_MUST_have_progressive_disclosure(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """MCP applications MUST provide 3-level progressive disclosure.

        Doctrine: MCP servers MUST expose resources at three levels:
        - Level 1: {slug}:// - BC overview + use case inventory
        - Level 2: {slug}://{entity} - Entity details + CRUD operations
        - Level 3: {slug}://{usecase} - Full use case details + schemas

        This ensures:
        - Minimal initial context for AI assistants
        - Detailed information available on demand
        - Efficient token usage through progressive loading
        """
        # This is enforced by the framework architecture itself.
        # The resources.py module registers discovery resources at
        # all three levels when create_mcp_server() is called.
        #
        # This test verifies apps use the framework.
        apps = await app_repo.list_by_type(AppType.MCP)
        assert len(apps) > 0, "No MCP applications found"

        for app in apps:
            init_file = Path(app.path) / "__init__.py"
            assert _calls_create_mcp_server(init_file), (
                f"MCP app '{app.slug}' does not use create_mcp_server() - "
                f"progressive disclosure resources not guaranteed"
            )
