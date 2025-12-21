"""MCP tools for DynamicStep CRUD operations."""

from julee.c4.domain.use_cases.requests import (
    CreateDynamicStepRequest,
    DeleteDynamicStepRequest,
    GetDynamicStepRequest,
    ListDynamicStepsRequest,
    UpdateDynamicStepRequest,
)
from apps.mcp.shared import ResponseFormat, format_entity, paginate_results
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


async def get_dynamic_step(slug: str, format: str = "full") -> dict:
    """Get a dynamic step by slug.

    Args:
        slug: Dynamic step slug
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with dynamic step data
    """
    use_case = get_get_dynamic_step_use_case()
    response = await use_case.execute(GetDynamicStepRequest(slug=slug))
    if not response.dynamic_step:
        return {"entity": None, "found": False}
    return {
        "entity": format_entity(
            response.dynamic_step.model_dump(),
            ResponseFormat.from_string(format),
            "dynamic_step",
        ),
        "found": True,
    }


async def list_dynamic_steps(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all dynamic steps with pagination.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with paginated dynamic steps list
    """
    use_case = get_list_dynamic_steps_use_case()
    response = await use_case.execute(ListDynamicStepsRequest())

    # Format entities based on requested verbosity
    fmt = ResponseFormat.from_string(format)
    all_entities = [
        format_entity(s.model_dump(), fmt, "dynamic_step")
        for s in response.dynamic_steps
    ]

    # Apply pagination
    return paginate_results(all_entities, limit=limit, offset=offset)


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
