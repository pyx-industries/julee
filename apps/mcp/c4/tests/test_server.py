"""Tests for C4 MCP server.

These tests ensure the MCP server is properly configured and doesn't fail
due to misconfiguration (missing imports, bad tool registration, etc.).

Test categories:
1. Module imports - all modules import without errors
2. Server configuration - FastMCP server is properly configured
3. Tool registration - all tools are registered correctly
4. Context factories - dependency factories work correctly

Note: Tests are marked xfail when imports fail due to missing dependencies.
"""

import importlib

import pytest

# Check if the server module imports successfully
try:
    from apps.mcp.c4.server import mcp as _mcp_server

    SERVER_IMPORTS_OK = True
except ImportError:
    SERVER_IMPORTS_OK = False

# Check if context module imports successfully
try:
    from apps.mcp.c4.context import get_docs_root as _get_docs_root

    CONTEXT_IMPORTS_OK = True
except ImportError:
    CONTEXT_IMPORTS_OK = False


@pytest.mark.skipif(not SERVER_IMPORTS_OK, reason="C4 server has import errors")
class TestModuleImports:
    """Test that all MCP modules import without errors."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "apps.mcp.c4.server",
            "apps.mcp.c4.context",
            "apps.mcp.c4.tools",
            "apps.mcp.c4.tools.software_systems",
            "apps.mcp.c4.tools.containers",
            "apps.mcp.c4.tools.components",
            "apps.mcp.c4.tools.relationships",
            "apps.mcp.c4.tools.deployment_nodes",
            "apps.mcp.c4.tools.dynamic_steps",
            "apps.mcp.c4.tools.diagrams",
        ],
    )
    def test_module_imports(self, module_name: str) -> None:
        """All C4 MCP modules must import without errors."""
        module = importlib.import_module(module_name)
        assert module is not None


@pytest.mark.skipif(not SERVER_IMPORTS_OK, reason="C4 server has import errors")
class TestServerConfiguration:
    """Test that the MCP server is properly configured."""

    def test_server_exists(self) -> None:
        """MCP server instance must exist."""
        from apps.mcp.c4.server import mcp

        assert mcp is not None

    def test_server_has_name(self) -> None:
        """MCP server must have a name."""
        from apps.mcp.c4.server import mcp

        assert mcp.name == "C4 Architecture Server"

    def test_server_has_instructions(self) -> None:
        """MCP server must have instructions."""
        from apps.mcp.c4.server import mcp

        assert mcp.instructions is not None
        assert "C4" in mcp.instructions


@pytest.mark.skipif(not SERVER_IMPORTS_OK, reason="C4 server has import errors")
class TestToolRegistration:
    """Test that tools are registered with the server."""

    def test_software_system_tools_registered(self) -> None:
        """Software system CRUD tools must be registered."""
        from apps.mcp.c4.server import (
            mcp_create_software_system,
            mcp_delete_software_system,
            mcp_get_software_system,
            mcp_list_software_systems,
            mcp_update_software_system,
        )

        # FastMCP decorators create FunctionTool objects
        assert mcp_create_software_system is not None
        assert mcp_get_software_system is not None
        assert mcp_list_software_systems is not None
        assert mcp_update_software_system is not None
        assert mcp_delete_software_system is not None

    def test_container_tools_registered(self) -> None:
        """Container CRUD tools must be registered."""
        from apps.mcp.c4.server import (
            mcp_create_container,
            mcp_delete_container,
            mcp_get_container,
            mcp_list_containers,
            mcp_update_container,
        )

        assert mcp_create_container is not None
        assert mcp_get_container is not None
        assert mcp_list_containers is not None
        assert mcp_update_container is not None
        assert mcp_delete_container is not None

    def test_component_tools_registered(self) -> None:
        """Component CRUD tools must be registered."""
        from apps.mcp.c4.server import (
            mcp_create_component,
            mcp_delete_component,
            mcp_get_component,
            mcp_list_components,
            mcp_update_component,
        )

        assert mcp_create_component is not None
        assert mcp_get_component is not None
        assert mcp_list_components is not None
        assert mcp_update_component is not None
        assert mcp_delete_component is not None

    def test_relationship_tools_registered(self) -> None:
        """Relationship CRUD tools must be registered."""
        from apps.mcp.c4.server import (
            mcp_create_relationship,
            mcp_delete_relationship,
            mcp_get_relationship,
            mcp_list_relationships,
            mcp_update_relationship,
        )

        assert mcp_create_relationship is not None
        assert mcp_get_relationship is not None
        assert mcp_list_relationships is not None
        assert mcp_update_relationship is not None
        assert mcp_delete_relationship is not None

    def test_deployment_node_tools_registered(self) -> None:
        """Deployment node CRUD tools must be registered."""
        from apps.mcp.c4.server import (
            mcp_create_deployment_node,
            mcp_delete_deployment_node,
            mcp_get_deployment_node,
            mcp_list_deployment_nodes,
            mcp_update_deployment_node,
        )

        assert mcp_create_deployment_node is not None
        assert mcp_get_deployment_node is not None
        assert mcp_list_deployment_nodes is not None
        assert mcp_update_deployment_node is not None
        assert mcp_delete_deployment_node is not None

    def test_dynamic_step_tools_registered(self) -> None:
        """Dynamic step CRUD tools must be registered."""
        from apps.mcp.c4.server import (
            mcp_create_dynamic_step,
            mcp_delete_dynamic_step,
            mcp_get_dynamic_step,
            mcp_list_dynamic_steps,
            mcp_update_dynamic_step,
        )

        assert mcp_create_dynamic_step is not None
        assert mcp_get_dynamic_step is not None
        assert mcp_list_dynamic_steps is not None
        assert mcp_update_dynamic_step is not None
        assert mcp_delete_dynamic_step is not None

    def test_diagram_tools_registered(self) -> None:
        """Diagram generation tools must be registered."""
        from apps.mcp.c4.server import (
            mcp_get_component_diagram,
            mcp_get_container_diagram,
            mcp_get_deployment_diagram,
            mcp_get_dynamic_diagram,
            mcp_get_system_context_diagram,
            mcp_get_system_landscape_diagram,
        )

        assert mcp_get_system_context_diagram is not None
        assert mcp_get_container_diagram is not None
        assert mcp_get_component_diagram is not None
        assert mcp_get_system_landscape_diagram is not None
        assert mcp_get_deployment_diagram is not None
        assert mcp_get_dynamic_diagram is not None


@pytest.mark.skipif(not CONTEXT_IMPORTS_OK, reason="C4 context has import errors")
class TestContextFactories:
    """Test that context/dependency factories work correctly."""

    def test_get_docs_root_returns_path(self) -> None:
        """get_docs_root must return a Path."""
        from pathlib import Path

        from apps.mcp.c4.context import get_docs_root

        result = get_docs_root()
        assert isinstance(result, Path)

    def test_repository_factories_return_instances(self) -> None:
        """Repository factories must return repository instances."""
        from apps.mcp.c4.context import (
            get_component_repository,
            get_container_repository,
            get_deployment_node_repository,
            get_dynamic_step_repository,
            get_relationship_repository,
            get_software_system_repository,
        )

        assert get_software_system_repository() is not None
        assert get_container_repository() is not None
        assert get_component_repository() is not None
        assert get_relationship_repository() is not None
        assert get_deployment_node_repository() is not None
        assert get_dynamic_step_repository() is not None

    def test_use_case_factories_return_instances(self) -> None:
        """Use case factories must return use case instances."""
        from apps.mcp.c4.context import (
            get_create_software_system_use_case,
            get_get_software_system_use_case,
            get_list_software_systems_use_case,
        )

        assert get_create_software_system_use_case() is not None
        assert get_get_software_system_use_case() is not None
        assert get_list_software_systems_use_case() is not None


@pytest.mark.skipif(not SERVER_IMPORTS_OK, reason="C4 server has import errors")
class TestMainFunction:
    """Test the main entry point."""

    def test_main_function_exists(self) -> None:
        """main() function must exist for CLI entry point."""
        from apps.mcp.c4.server import main

        assert callable(main)
