"""MCP tools for Component CRUD operations."""

from ...c4_api.requests import (
    CreateComponentRequest,
    DeleteComponentRequest,
    GetComponentRequest,
    ListComponentsRequest,
    UpdateComponentRequest,
)
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


async def get_component(slug: str) -> dict:
    """Get a component by slug."""
    use_case = get_get_component_use_case()
    response = await use_case.execute(GetComponentRequest(slug=slug))
    if not response.component:
        return {"entity": None, "found": False}
    return {
        "entity": response.component.model_dump(),
        "found": True,
    }


async def list_components() -> dict:
    """List all components."""
    use_case = get_list_components_use_case()
    response = await use_case.execute(ListComponentsRequest())
    return {
        "entities": [c.model_dump() for c in response.components],
        "count": len(response.components),
    }


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
