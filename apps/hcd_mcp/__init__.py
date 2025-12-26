"""HCD MCP Server Application.

Human-Centered Design MCP server built with the julee MCP framework.
"""

from julee import hcd
from julee.core.infrastructure.mcp import create_mcp_server

from . import context

mcp = create_mcp_server(
    slug="hcd",
    domain_module=hcd,
    context_module=context,
)


def main() -> None:
    """Run the HCD MCP server."""
    mcp.run()
