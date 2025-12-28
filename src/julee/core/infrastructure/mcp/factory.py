"""MCP server factory.

Creates doctrine-compliant MCP servers from domain modules.
"""

from types import ModuleType

from fastmcp import FastMCP

from .discovery import build_service_config, get_module_summary
from .resources import register_discovery_resources
from .tool_factory import register_tools


def create_mcp_server(
    slug: str,
    domain_module: ModuleType,
    context_module: ModuleType,
    name: str | None = None,
) -> FastMCP:
    """Create a doctrine-compliant MCP server from a domain module.

    Automatically sets up:
    - 3-level progressive disclosure resources ({slug}://)
    - Tools derived from use cases with minimal docstrings
    - Diagram consolidation (if applicable)

    Args:
        slug: Service identifier (e.g. 'c4', 'hcd')
        domain_module: The domain module (e.g. julee.c4)
        context_module: Module with DI factory functions
        name: Optional display name (defaults to slug)

    Returns:
        Configured FastMCP server instance
    """
    # Build service configuration by discovering use cases
    config = build_service_config(slug, domain_module, context_module)

    # Create MCP server with minimal instructions
    module_summary = get_module_summary(domain_module)
    mcp = FastMCP(
        name or slug,
        instructions=f"{module_summary} Read {slug}:// for capabilities.",
    )

    # Register 3-level progressive disclosure resources
    register_discovery_resources(mcp, config)

    # Register tools from discovered use cases
    register_tools(mcp, config)

    return mcp
