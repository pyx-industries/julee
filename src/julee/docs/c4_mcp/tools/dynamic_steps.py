"""MCP tools for DynamicStep CRUD operations."""

from ...c4_api.requests import (
    CreateDynamicStepRequest,
    DeleteDynamicStepRequest,
    GetDynamicStepRequest,
    ListDynamicStepsRequest,
    UpdateDynamicStepRequest,
)
from ..context import (
    get_create_dynamic_step_use_case,
    get_delete_dynamic_step_use_case,
    get_get_dynamic_step_use_case,
    get_list_dynamic_steps_use_case,
    get_update_dynamic_step_use_case,
)


async def create_dynamic_step(
    sequence_name: str,
    step_number: int,
    source_type: str,
    source_slug: str,
    destination_type: str,
    destination_slug: str,
    slug: str = "",
    description: str = "",
    technology: str = "",
    return_description: str = "",
    is_return: bool = False,
) -> dict:
    """Create a new dynamic step."""
    use_case = get_create_dynamic_step_use_case()
    request = CreateDynamicStepRequest(
        slug=slug,
        sequence_name=sequence_name,
        step_number=step_number,
        source_type=source_type,
        source_slug=source_slug,
        destination_type=destination_type,
        destination_slug=destination_slug,
        description=description,
        technology=technology,
        return_description=return_description,
        is_return=is_return,
    )
    response = await use_case.execute(request)
    return {
        "success": True,
        "entity": response.dynamic_step.model_dump(),
    }


async def get_dynamic_step(slug: str) -> dict:
    """Get a dynamic step by slug."""
    use_case = get_get_dynamic_step_use_case()
    response = await use_case.execute(GetDynamicStepRequest(slug=slug))
    if not response.dynamic_step:
        return {"entity": None, "found": False}
    return {
        "entity": response.dynamic_step.model_dump(),
        "found": True,
    }


async def list_dynamic_steps() -> dict:
    """List all dynamic steps."""
    use_case = get_list_dynamic_steps_use_case()
    response = await use_case.execute(ListDynamicStepsRequest())
    return {
        "entities": [s.model_dump() for s in response.dynamic_steps],
        "count": len(response.dynamic_steps),
    }


async def update_dynamic_step(
    slug: str,
    step_number: int | None = None,
    description: str | None = None,
    technology: str | None = None,
    return_description: str | None = None,
    is_return: bool | None = None,
) -> dict:
    """Update an existing dynamic step."""
    use_case = get_update_dynamic_step_use_case()
    request = UpdateDynamicStepRequest(
        slug=slug,
        step_number=step_number,
        description=description,
        technology=technology,
        return_description=return_description,
        is_return=is_return,
    )
    response = await use_case.execute(request)
    if not response.found:
        return {"success": False, "entity": None}
    return {
        "success": True,
        "entity": response.dynamic_step.model_dump() if response.dynamic_step else None,
    }


async def delete_dynamic_step(slug: str) -> dict:
    """Delete a dynamic step by slug."""
    use_case = get_delete_dynamic_step_use_case()
    response = await use_case.execute(DeleteDynamicStepRequest(slug=slug))
    return {"success": response.deleted, "entity": None}
