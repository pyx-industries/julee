"""MCP tools for SoftwareSystem CRUD operations."""

from ...c4_api.requests import (
    CreateSoftwareSystemRequest,
    DeleteSoftwareSystemRequest,
    GetSoftwareSystemRequest,
    ListSoftwareSystemsRequest,
    UpdateSoftwareSystemRequest,
)
from ...mcp_shared import ResponseFormat, format_entity, paginate_results
from ..context import (
    get_create_software_system_use_case,
    get_delete_software_system_use_case,
    get_get_software_system_use_case,
    get_list_software_systems_use_case,
    get_update_software_system_use_case,
)


async def create_software_system(
    slug: str,
    name: str,
    description: str = "",
    system_type: str = "internal",
    owner: str = "",
    technology: str = "",
    url: str = "",
    tags: list[str] | None = None,
) -> dict:
    """Create a new software system."""
    use_case = get_create_software_system_use_case()
    request = CreateSoftwareSystemRequest(
        slug=slug,
        name=name,
        description=description,
        system_type=system_type,
        owner=owner,
        technology=technology,
        url=url,
        tags=tags or [],
    )
    response = await use_case.execute(request)
    return {
        "success": True,
        "entity": response.software_system.model_dump(),
    }


async def get_software_system(slug: str, format: str = "full") -> dict:
    """Get a software system by slug.

    Args:
        slug: Software system slug
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with software system data
    """
    use_case = get_get_software_system_use_case()
    response = await use_case.execute(GetSoftwareSystemRequest(slug=slug))
    if not response.software_system:
        return {"entity": None, "found": False}
    return {
        "entity": format_entity(
            response.software_system.model_dump(),
            ResponseFormat.from_string(format),
            "software_system",
        ),
        "found": True,
    }


async def list_software_systems(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all software systems with pagination.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with paginated software systems list
    """
    use_case = get_list_software_systems_use_case()
    response = await use_case.execute(ListSoftwareSystemsRequest())

    # Format entities based on requested verbosity
    fmt = ResponseFormat.from_string(format)
    all_entities = [
        format_entity(s.model_dump(), fmt, "software_system")
        for s in response.software_systems
    ]

    # Apply pagination
    return paginate_results(all_entities, limit=limit, offset=offset)


async def update_software_system(
    slug: str,
    name: str | None = None,
    description: str | None = None,
    system_type: str | None = None,
    owner: str | None = None,
    technology: str | None = None,
    url: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Update an existing software system."""
    use_case = get_update_software_system_use_case()
    request = UpdateSoftwareSystemRequest(
        slug=slug,
        name=name,
        description=description,
        system_type=system_type,
        owner=owner,
        technology=technology,
        url=url,
        tags=tags,
    )
    response = await use_case.execute(request)
    if not response.found:
        return {"success": False, "entity": None}
    return {
        "success": True,
        "entity": (
            response.software_system.model_dump() if response.software_system else None
        ),
    }


async def delete_software_system(slug: str) -> dict:
    """Delete a software system by slug."""
    use_case = get_delete_software_system_use_case()
    response = await use_case.execute(DeleteSoftwareSystemRequest(slug=slug))
    return {"success": response.deleted, "entity": None}
