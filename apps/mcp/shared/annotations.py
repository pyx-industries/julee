"""Tool annotation factories for MCP servers.

Provides semantic annotation builders for consistent tool classification.
These annotations communicate tool behavior to MCP clients without consuming
token context, enabling features like:
- Auto-approval of safe operations (readOnlyHint)
- Confirmation prompts for destructive operations (destructiveHint)
- Safe retry behavior (idempotentHint)

Usage:
    from apps.mcp.shared import read_only_annotation

    @mcp.tool(annotations=read_only_annotation("List Stories"))
    async def mcp_list_stories() -> dict:
        ...
"""

from mcp.types import ToolAnnotations


def read_only_annotation(title: str | None = None) -> ToolAnnotations:
    """Annotation for list/get operations that don't modify state.

    Characteristics:
    - readOnlyHint=True: Safe to execute without confirmation
    - destructiveHint=False: No data is modified
    - idempotentHint=True: Same result on repeated calls

    Args:
        title: Human-readable display name for the tool
    """
    return ToolAnnotations(
        title=title,
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )


def create_annotation(title: str | None = None) -> ToolAnnotations:
    """Annotation for create operations (additive, not idempotent).

    Characteristics:
    - readOnlyHint=False: Modifies state
    - destructiveHint=False: Additive only, doesn't remove/overwrite
    - idempotentHint=False: Creates new entity each time

    Args:
        title: Human-readable display name for the tool
    """
    return ToolAnnotations(
        title=title,
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    )


def update_annotation(title: str | None = None) -> ToolAnnotations:
    """Annotation for update operations (idempotent, potentially destructive).

    Characteristics:
    - readOnlyHint=False: Modifies state
    - destructiveHint=True: Overwrites existing data
    - idempotentHint=True: Same input produces same result

    Args:
        title: Human-readable display name for the tool
    """
    return ToolAnnotations(
        title=title,
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )


def delete_annotation(title: str | None = None) -> ToolAnnotations:
    """Annotation for delete operations (destructive, idempotent).

    Characteristics:
    - readOnlyHint=False: Modifies state
    - destructiveHint=True: Removes data permanently
    - idempotentHint=True: Double-delete is a no-op

    Args:
        title: Human-readable display name for the tool
    """
    return ToolAnnotations(
        title=title,
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )


def diagram_annotation(title: str | None = None) -> ToolAnnotations:
    """Annotation for diagram generation (read-only, computed).

    Used for C4 diagram tools that generate visualizations from existing data.

    Characteristics:
    - readOnlyHint=True: Safe to execute without confirmation
    - destructiveHint=False: No data is modified
    - idempotentHint=True: Same result on repeated calls

    Args:
        title: Human-readable display name for the tool
    """
    return ToolAnnotations(
        title=title,
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
