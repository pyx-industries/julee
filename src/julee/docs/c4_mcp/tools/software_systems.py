"""MCP tools for SoftwareSystem CRUD operations."""

from ...c4_api.requests import (
    CreateSoftwareSystemRequest,
    DeleteSoftwareSystemRequest,
    GetSoftwareSystemRequest,
    ListSoftwareSystemsRequest,
    UpdateSoftwareSystemRequest,
)
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


async def get_software_system(slug: str) -> dict:
    """Get a software system by slug."""
    use_case = get_get_software_system_use_case()
    response = await use_case.execute(GetSoftwareSystemRequest(slug=slug))
    if not response.software_system:
        return {"entity": None, "found": False}
    return {
        "entity": response.software_system.model_dump(),
        "found": True,
    }


async def list_software_systems() -> dict:
    """List all software systems."""
    use_case = get_list_software_systems_use_case()
    response = await use_case.execute(ListSoftwareSystemsRequest())
    return {
        "entities": [s.model_dump() for s in response.software_systems],
        "count": len(response.software_systems),
    }


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
        "entity": response.software_system.model_dump() if response.software_system else None,
    }


async def delete_software_system(slug: str) -> dict:
    """Delete a software system by slug."""
    use_case = get_delete_software_system_use_case()
    response = await use_case.execute(DeleteSoftwareSystemRequest(slug=slug))
    return {"success": response.deleted, "entity": None}
