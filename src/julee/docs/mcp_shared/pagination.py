"""Pagination utilities for MCP server responses.

Provides consistent pagination across list operations, enabling agents to
efficiently work with large result sets without consuming excessive tokens.

Usage:
    from julee.docs.mcp_shared import paginate_results

    @mcp.tool()
    async def mcp_list_stories(limit: int | None = None, offset: int = 0) -> dict:
        all_stories = get_all_stories()
        return paginate_results(
            items=[s.model_dump() for s in all_stories],
            limit=limit,
            offset=offset,
        )
"""

from typing import Any

# Default and maximum limits for pagination
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000


def paginate_results(
    items: list[Any],
    limit: int | None = None,
    offset: int = 0,
) -> dict[str, Any]:
    """Paginate a list of items with metadata.

    Args:
        items: Full list of items to paginate
        limit: Maximum items to return (None = DEFAULT_LIMIT, capped at MAX_LIMIT)
        offset: Number of items to skip from start

    Returns:
        Dict with paginated results and metadata:
        - entities: The paginated slice of items
        - count: Number of items in this response
        - pagination: Metadata dict with total, limit, offset, has_more
        - efficiency_hint: Optional hint when result set is large
    """
    total = len(items)

    # Apply limit bounds
    effective_limit = min(limit or DEFAULT_LIMIT, MAX_LIMIT)

    # Clamp offset to valid range
    effective_offset = max(0, min(offset, total))

    # Slice the items
    end_index = effective_offset + effective_limit
    paginated_items = items[effective_offset:end_index]

    has_more = end_index < total

    result: dict[str, Any] = {
        "entities": paginated_items,
        "count": len(paginated_items),
        "pagination": {
            "total": total,
            "limit": effective_limit,
            "offset": effective_offset,
            "has_more": has_more,
        },
    }

    # Add efficiency hint for large result sets
    if total > 50 and has_more:
        result["efficiency_hint"] = (
            f"{total} total items. Use offset={end_index} to fetch next page, "
            "or apply filters to narrow results."
        )

    return result


def get_pagination_params_description() -> str:
    """Return standard docstring text for pagination parameters.

    Use this to maintain consistent documentation across list operations.
    """
    return f"""    limit: Maximum results to return (1-{MAX_LIMIT}, default {DEFAULT_LIMIT})
        offset: Skip first N results for pagination (default 0)"""
