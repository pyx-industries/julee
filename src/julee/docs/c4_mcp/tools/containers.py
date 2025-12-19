"""MCP tools for Container CRUD operations."""

from ...c4_api.requests import (
    CreateContainerRequest,
    DeleteContainerRequest,
    GetContainerRequest,
    ListContainersRequest,
    UpdateContainerRequest,
)
from ..context import (
    get_create_container_use_case,
    get_delete_container_use_case,
    get_get_container_use_case,
    get_list_containers_use_case,
    get_update_container_use_case,
)


async def create_container(
    slug: str,
    name: str,
    system_slug: str,
    description: str = "",
    container_type: str = "other",
    technology: str = "",
    url: str = "",
    tags: list[str] | None = None,
) -> dict:
    """Create a new container."""
    use_case = get_create_container_use_case()
    request = CreateContainerRequest(
        slug=slug,
        name=name,
        system_slug=system_slug,
        description=description,
        container_type=container_type,
        technology=technology,
        url=url,
        tags=tags or [],
    )
    response = await use_case.execute(request)
    return {
        "success": True,
        "entity": response.container.model_dump(),
    }


async def get_container(slug: str) -> dict:
    """Get a container by slug."""
    use_case = get_get_container_use_case()
    response = await use_case.execute(GetContainerRequest(slug=slug))
    if not response.container:
        return {"entity": None, "found": False}
    return {
        "entity": response.container.model_dump(),
        "found": True,
    }


async def list_containers() -> dict:
    """List all containers."""
    use_case = get_list_containers_use_case()
    response = await use_case.execute(ListContainersRequest())
    return {
        "entities": [c.model_dump() for c in response.containers],
        "count": len(response.containers),
    }


async def update_container(
    slug: str,
    name: str | None = None,
    system_slug: str | None = None,
    description: str | None = None,
    container_type: str | None = None,
    technology: str | None = None,
    url: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Update an existing container."""
    use_case = get_update_container_use_case()
    request = UpdateContainerRequest(
        slug=slug,
        name=name,
        system_slug=system_slug,
        description=description,
        container_type=container_type,
        technology=technology,
        url=url,
        tags=tags,
    )
    response = await use_case.execute(request)
    if not response.found:
        return {"success": False, "entity": None}
    return {
        "success": True,
        "entity": response.container.model_dump() if response.container else None,
    }


async def delete_container(slug: str) -> dict:
    """Delete a container by slug."""
    use_case = get_delete_container_use_case()
    response = await use_case.execute(DeleteContainerRequest(slug=slug))
    return {"success": response.deleted, "entity": None}
