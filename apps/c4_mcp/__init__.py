"""C4 MCP Server Application.

C4 Architecture Model MCP server built with the julee MCP framework.
"""

from julee import c4
from julee.core.infrastructure.mcp import create_mcp_server

from . import context

mcp = create_mcp_server(
    slug="c4",
    domain_module=c4,
    context_module=context,
)


def main() -> None:
    """Run the C4 MCP server."""
    mcp.run()
