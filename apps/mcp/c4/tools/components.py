"""MCP tools for Component CRUD operations."""

from julee.c4.domain.use_cases.requests import (
    CreateComponentRequest,
    DeleteComponentRequest,
    GetComponentRequest,
    ListComponentsRequest,
    UpdateComponentRequest,
)
from apps.mcp.shared import ResponseFormat, format_entity, paginate_results
from ..context import (
    get_create_component_use_case,
    get_delete_component_use_case,
    get_get_component_use_case,
    get_list_components_use_case,
    get_update_component_use_case,
)


async def create_component(
    slug: str,
    name: str,
    container_slug: str,
    system_slug: str,
    description: str = "",
    technology: str = "",
    interface: str = "",
    code_path: str = "",
    url: str = "",
    tags: list[str] | None = None,
) -> dict:
    """Create a new component."""
    use_case = get_create_component_use_case()
    request = CreateComponentRequest(
        slug=slug,
        name=name,
        container_slug=container_slug,
        system_slug=system_slug,
        description=description,
        technology=technology,
        interface=interface,
        code_path=code_path,
        url=url,
        tags=tags or [],
    )
    response = await use_case.execute(request)
    return {
        "success": True,
        "entity": response.component.model_dump(),
    }


async def get_component(slug: str, format: str = "full") -> dict:
    """Get a component by slug.

    Args:
        slug: Component slug
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with component data
    """
    use_case = get_get_component_use_case()
    response = await use_case.execute(GetComponentRequest(slug=slug))
    if not response.component:
        return {"entity": None, "found": False}
    return {
        "entity": format_entity(
            response.component.model_dump(),
            ResponseFormat.from_string(format),
            "component",
        ),
        "found": True,
    }


async def list_components(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all components with pagination.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with paginated components list
    """
    use_case = get_list_components_use_case()
    response = await use_case.execute(ListComponentsRequest())

    # Format entities based on requested verbosity
    fmt = ResponseFormat.from_string(format)
    all_entities = [
        format_entity(c.model_dump(), fmt, "component") for c in response.components
    ]

    # Apply pagination
    return paginate_results(all_entities, limit=limit, offset=offset)


async def update_component(
    slug: str,
    name: str | None = None,
    container_slug: str | None = None,
    system_slug: str | None = None,
    description: str | None = None,
    technology: str | None = None,
    interface: str | None = None,
    code_path: str | None = None,
    url: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Update an existing component."""
    use_case = get_update_component_use_case()
    request = UpdateComponentRequest(
        slug=slug,
        name=name,
        container_slug=container_slug,
        system_slug=system_slug,
        description=description,
        technology=technology,
        interface=interface,
        code_path=code_path,
        url=url,
        tags=tags,
    )
    response = await use_case.execute(request)
    if not response.found:
        return {"success": False, "entity": None}
    return {
        "success": True,
        "entity": response.component.model_dump() if response.component else None,
    }


async def delete_component(slug: str) -> dict:
    """Delete a component by slug."""
    use_case = get_delete_component_use_case()
    response = await use_case.execute(DeleteComponentRequest(slug=slug))
    return {"success": response.deleted, "entity": None}
