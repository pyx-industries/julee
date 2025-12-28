"""MCP server framework for Julee.

Provides automatic MCP server generation from domain use cases
with 3-level progressive disclosure for documentation.

Usage:
    from julee.core.infrastructure.mcp.factory import create_mcp_server
    from julee import c4
    from . import context

    mcp = create_mcp_server(
        slug="c4",
        domain_module=c4,
        context_module=context,
    )

    def main():
        mcp.run()
"""
