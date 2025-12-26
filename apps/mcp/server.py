"""Combined MCP server for all Julee accelerators."""

from fastmcp import FastMCP

mcp = FastMCP("julee")


def register_all_tools() -> None:
    """Register all HCD and C4 tools with the MCP server."""
    from .c4.tools import register_tools as register_c4_tools
    from .hcd.tools import register_tools as register_hcd_tools

    register_hcd_tools(mcp)
    register_c4_tools(mcp)


def main() -> None:
    """Run the combined MCP server."""
    register_all_tools()
    mcp.run()


if __name__ == "__main__":
    main()
