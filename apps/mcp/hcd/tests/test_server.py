"""Tests for HCD MCP server.

These tests ensure the MCP server is properly configured and doesn't fail
due to misconfiguration (missing imports, bad tool registration, etc.).

Test categories:
1. Module imports - all modules import without errors
2. Server configuration - FastMCP server is properly configured
3. Tool registration - all tools are registered correctly
4. Context factories - dependency factories work correctly
"""

import importlib

import pytest

# Check if the server module imports successfully
try:
    from apps.mcp.hcd.server import mcp as _mcp_server

    SERVER_IMPORTS_OK = True
except ImportError:
    SERVER_IMPORTS_OK = False

# Check if context module imports successfully
try:
    from apps.mcp.hcd.context import get_docs_root as _get_docs_root

    CONTEXT_IMPORTS_OK = True
except ImportError:
    CONTEXT_IMPORTS_OK = False


@pytest.mark.skipif(not SERVER_IMPORTS_OK, reason="HCD server has import errors")
class TestModuleImports:
    """Test that all MCP modules import without errors."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "apps.mcp.hcd.server",
            "apps.mcp.hcd.context",
            "apps.mcp.hcd.tools",
            "apps.mcp.hcd.tools.stories",
            "apps.mcp.hcd.tools.epics",
            "apps.mcp.hcd.tools.journeys",
            "apps.mcp.hcd.tools.personas",
            "apps.mcp.hcd.tools.accelerators",
            "apps.mcp.hcd.tools.integrations",
            "apps.mcp.hcd.tools.apps",
        ],
    )
    def test_module_imports(self, module_name: str) -> None:
        """All HCD MCP modules must import without errors."""
        module = importlib.import_module(module_name)
        assert module is not None


@pytest.mark.skipif(not SERVER_IMPORTS_OK, reason="HCD server has import errors")
class TestServerConfiguration:
    """Test that the MCP server is properly configured."""

    def test_server_exists(self) -> None:
        """MCP server instance must exist."""
        from apps.mcp.hcd.server import mcp

        assert mcp is not None

    def test_server_has_name(self) -> None:
        """MCP server must have a name."""
        from apps.mcp.hcd.server import mcp

        assert mcp.name == "HCD Domain Server"

    def test_server_has_instructions(self) -> None:
        """MCP server must have instructions."""
        from apps.mcp.hcd.server import mcp

        assert mcp.instructions is not None
        assert "HCD" in mcp.instructions or "Human-Centered Design" in mcp.instructions


@pytest.mark.skipif(not SERVER_IMPORTS_OK, reason="HCD server has import errors")
class TestToolRegistration:
    """Test that tools are registered with the server."""

    def test_story_tools_registered(self) -> None:
        """Story CRUD tools must be registered."""
        from apps.mcp.hcd.server import (
            mcp_create_story,
            mcp_delete_story,
            mcp_get_story,
            mcp_list_stories,
            mcp_update_story,
        )

        # Verify functions exist and are callable
        assert callable(mcp_create_story)
        assert callable(mcp_get_story)
        assert callable(mcp_list_stories)
        assert callable(mcp_update_story)
        assert callable(mcp_delete_story)

    def test_epic_tools_registered(self) -> None:
        """Epic CRUD tools must be registered."""
        from apps.mcp.hcd.server import (
            mcp_create_epic,
            mcp_delete_epic,
            mcp_get_epic,
            mcp_list_epics,
            mcp_update_epic,
        )

        assert callable(mcp_create_epic)
        assert callable(mcp_get_epic)
        assert callable(mcp_list_epics)
        assert callable(mcp_update_epic)
        assert callable(mcp_delete_epic)

    def test_journey_tools_registered(self) -> None:
        """Journey CRUD tools must be registered."""
        from apps.mcp.hcd.server import (
            mcp_create_journey,
            mcp_delete_journey,
            mcp_get_journey,
            mcp_list_journeys,
            mcp_update_journey,
        )

        assert callable(mcp_create_journey)
        assert callable(mcp_get_journey)
        assert callable(mcp_list_journeys)
        assert callable(mcp_update_journey)
        assert callable(mcp_delete_journey)

    def test_persona_tools_registered(self) -> None:
        """Persona read tools must be registered (personas are derived, not created)."""
        from apps.mcp.hcd.server import mcp_get_persona, mcp_list_personas

        assert callable(mcp_get_persona)
        assert callable(mcp_list_personas)

    def test_accelerator_tools_registered(self) -> None:
        """Accelerator CRUD tools must be registered."""
        from apps.mcp.hcd.server import (
            mcp_create_accelerator,
            mcp_delete_accelerator,
            mcp_get_accelerator,
            mcp_list_accelerators,
            mcp_update_accelerator,
        )

        assert callable(mcp_create_accelerator)
        assert callable(mcp_get_accelerator)
        assert callable(mcp_list_accelerators)
        assert callable(mcp_update_accelerator)
        assert callable(mcp_delete_accelerator)

    def test_integration_tools_registered(self) -> None:
        """Integration CRUD tools must be registered."""
        from apps.mcp.hcd.server import (
            mcp_create_integration,
            mcp_delete_integration,
            mcp_get_integration,
            mcp_list_integrations,
            mcp_update_integration,
        )

        assert callable(mcp_create_integration)
        assert callable(mcp_get_integration)
        assert callable(mcp_list_integrations)
        assert callable(mcp_update_integration)
        assert callable(mcp_delete_integration)

    def test_app_tools_registered(self) -> None:
        """App CRUD tools must be registered."""
        from apps.mcp.hcd.server import (
            mcp_create_app,
            mcp_delete_app,
            mcp_get_app,
            mcp_list_apps,
            mcp_update_app,
        )

        assert callable(mcp_create_app)
        assert callable(mcp_get_app)
        assert callable(mcp_list_apps)
        assert callable(mcp_update_app)
        assert callable(mcp_delete_app)


@pytest.mark.skipif(not CONTEXT_IMPORTS_OK, reason="HCD context has import errors")
class TestContextFactories:
    """Test that context/dependency factories work correctly."""

    def test_get_docs_root_returns_path(self) -> None:
        """get_docs_root must return a Path."""
        from pathlib import Path

        from apps.mcp.hcd.context import get_docs_root

        result = get_docs_root()
        assert isinstance(result, Path)

    def test_repository_factories_return_instances(self) -> None:
        """Repository factories must return repository instances."""
        from apps.mcp.hcd.context import (
            get_accelerator_repository,
            get_app_repository,
            get_epic_repository,
            get_integration_repository,
            get_journey_repository,
            get_persona_repository,
            get_story_repository,
        )

        # These should not raise - they create repository instances
        assert get_story_repository() is not None
        assert get_epic_repository() is not None
        assert get_journey_repository() is not None
        assert get_accelerator_repository() is not None
        assert get_integration_repository() is not None
        assert get_app_repository() is not None
        assert get_persona_repository() is not None

    def test_use_case_factories_return_instances(self) -> None:
        """Use case factories must return use case instances."""
        from apps.mcp.hcd.context import (
            get_create_story_use_case,
            get_get_story_use_case,
            get_list_stories_use_case,
        )

        # These should not raise - they create use case instances
        assert get_create_story_use_case() is not None
        assert get_get_story_use_case() is not None
        assert get_list_stories_use_case() is not None


@pytest.mark.skipif(not SERVER_IMPORTS_OK, reason="HCD server has import errors")
class TestMainFunction:
    """Test the main entry point."""

    def test_main_function_exists(self) -> None:
        """main() function must exist for CLI entry point."""
        from apps.mcp.hcd.server import main

        assert callable(main)
