"""Core MCP Server Application.

Core bounded context MCP server built with the julee MCP framework.
"""

from julee import core
from julee.core.infrastructure.mcp import create_mcp_server

from . import context

mcp = create_mcp_server(
    slug="core",
    domain_module=core,
    context_module=context,
)


def main() -> None:
    """Run the Core MCP server."""
    mcp.run()
