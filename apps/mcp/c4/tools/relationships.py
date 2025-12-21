"""MCP tools for Relationship CRUD operations."""

from julee.c4.domain.use_cases.requests import (
    CreateRelationshipRequest,
    DeleteRelationshipRequest,
    GetRelationshipRequest,
    ListRelationshipsRequest,
    UpdateRelationshipRequest,
)
from apps.mcp.shared import ResponseFormat, format_entity, paginate_results
from ..context import (
    get_create_relationship_use_case,
    get_delete_relationship_use_case,
    get_get_relationship_use_case,
    get_list_relationships_use_case,
    get_update_relationship_use_case,
)


async def create_relationship(
    source_type: str,
    source_slug: str,
    destination_type: str,
    destination_slug: str,
    slug: str = "",
    description: str = "Uses",
    technology: str = "",
    bidirectional: bool = False,
    tags: list[str] | None = None,
) -> dict:
    """Create a new relationship."""
    use_case = get_create_relationship_use_case()
    request = CreateRelationshipRequest(
        slug=slug,
        source_type=source_type,
        source_slug=source_slug,
        destination_type=destination_type,
        destination_slug=destination_slug,
        description=description,
        technology=technology,
        bidirectional=bidirectional,
        tags=tags or [],
    )
    response = await use_case.execute(request)
    return {
        "success": True,
        "entity": response.relationship.model_dump(),
    }


async def get_relationship(slug: str, format: str = "full") -> dict:
    """Get a relationship by slug.

    Args:
        slug: Relationship slug
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with relationship data
    """
    use_case = get_get_relationship_use_case()
    response = await use_case.execute(GetRelationshipRequest(slug=slug))
    if not response.relationship:
        return {"entity": None, "found": False}
    return {
        "entity": format_entity(
            response.relationship.model_dump(),
            ResponseFormat.from_string(format),
            "relationship",
        ),
        "found": True,
    }


async def list_relationships(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all relationships with pagination.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with paginated relationships list
    """
    use_case = get_list_relationships_use_case()
    response = await use_case.execute(ListRelationshipsRequest())

    # Format entities based on requested verbosity
    fmt = ResponseFormat.from_string(format)
    all_entities = [
        format_entity(r.model_dump(), fmt, "relationship")
        for r in response.relationships
    ]

    # Apply pagination
    return paginate_results(all_entities, limit=limit, offset=offset)


async def update_relationship(
    slug: str,
    description: str | None = None,
    technology: str | None = None,
    bidirectional: bool | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Update an existing relationship."""
    use_case = get_update_relationship_use_case()
    request = UpdateRelationshipRequest(
        slug=slug,
        description=description,
        technology=technology,
        bidirectional=bidirectional,
        tags=tags,
    )
    response = await use_case.execute(request)
    if not response.found:
        return {"success": False, "entity": None}
    return {
        "success": True,
        "entity": response.relationship.model_dump() if response.relationship else None,
    }


async def delete_relationship(slug: str) -> dict:
    """Delete a relationship by slug."""
    use_case = get_delete_relationship_use_case()
    response = await use_case.execute(DeleteRelationshipRequest(slug=slug))
    return {"success": response.deleted, "entity": None}
