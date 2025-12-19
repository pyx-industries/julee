"""MCP tools for Epic CRUD operations.

All operations delegate to use-case classes following clean architecture.
Responses include contextual suggestions based on domain semantics.
"""

from ...hcd_api.requests import (
    CreateEpicRequest,
    DeleteEpicRequest,
    GetEpicRequest,
    ListEpicsRequest,
    UpdateEpicRequest,
)
from ...sphinx_hcd.domain.use_cases.suggestions import compute_epic_suggestions
from ..context import (
    get_create_epic_use_case,
    get_delete_epic_use_case,
    get_get_epic_use_case,
    get_list_epics_use_case,
    get_suggestion_context,
    get_update_epic_use_case,
)


async def create_epic(
    slug: str,
    description: str = "",
    story_refs: list[str] | None = None,
) -> dict:
    """Create a new epic.

    Args:
        slug: Epic slug (URL-safe identifier)
        description: Epic description
        story_refs: List of story titles in this epic

    Returns:
        Response with created epic and contextual suggestions
    """
    use_case = get_create_epic_use_case()
    request = CreateEpicRequest(
        slug=slug,
        description=description,
        story_refs=story_refs or [],
    )
    response = await use_case.execute(request)

    # Compute suggestions
    ctx = get_suggestion_context()
    suggestions = await compute_epic_suggestions(response.epic, ctx)

    return {
        "success": True,
        "entity": response.epic.model_dump(),
        "suggestions": suggestions,
    }


async def get_epic(slug: str) -> dict:
    """Get an epic by its slug.

    Args:
        slug: Epic slug

    Returns:
        Response with epic data and contextual suggestions
    """
    use_case = get_get_epic_use_case()
    response = await use_case.execute(GetEpicRequest(slug=slug))

    if not response.epic:
        return {
            "entity": None,
            "found": False,
            "suggestions": [],
        }

    # Compute suggestions
    ctx = get_suggestion_context()
    suggestions = await compute_epic_suggestions(response.epic, ctx)

    return {
        "entity": response.epic.model_dump(),
        "found": True,
        "suggestions": suggestions,
    }


async def list_epics() -> dict:
    """List all epics.

    Returns:
        Response with epics list and aggregate suggestions
    """
    use_case = get_list_epics_use_case()
    response = await use_case.execute(ListEpicsRequest())

    # Compute aggregate suggestions
    suggestions = []

    # Count epics without stories
    empty_epics = [e for e in response.epics if not e.story_refs]
    if empty_epics:
        suggestions.append({
            "severity": "warning",
            "category": "incomplete",
            "message": f"{len(empty_epics)} epics have no stories defined",
            "action": "Add story references to these epics",
            "tool": "update_epic",
            "context": {"empty_epic_slugs": [e.slug for e in empty_epics[:10]]},
        })

    # Summary info
    total_story_refs = sum(len(e.story_refs) for e in response.epics)
    if response.epics:
        suggestions.append({
            "severity": "info",
            "category": "relationship",
            "message": f"{len(response.epics)} epics reference {total_story_refs} stories",
            "action": "Review story coverage across epics",
            "tool": "list_stories",
            "context": {"epic_count": len(response.epics), "story_ref_count": total_story_refs},
        })

    return {
        "entities": [e.model_dump() for e in response.epics],
        "count": len(response.epics),
        "suggestions": suggestions,
    }


async def update_epic(
    slug: str,
    description: str | None = None,
    story_refs: list[str] | None = None,
) -> dict:
    """Update an existing epic.

    Args:
        slug: Epic slug to update
        description: New description (optional)
        story_refs: New story refs (optional)

    Returns:
        Response with updated epic and contextual suggestions
    """
    use_case = get_update_epic_use_case()
    request = UpdateEpicRequest(
        slug=slug,
        description=description,
        story_refs=story_refs,
    )
    response = await use_case.execute(request)

    if not response.found:
        return {
            "success": False,
            "entity": None,
            "suggestions": [],
        }

    # Compute suggestions
    ctx = get_suggestion_context()
    suggestions = await compute_epic_suggestions(response.epic, ctx) if response.epic else []

    return {
        "success": True,
        "entity": response.epic.model_dump() if response.epic else None,
        "suggestions": suggestions,
    }


async def delete_epic(slug: str) -> dict:
    """Delete an epic by slug.

    Args:
        slug: Epic slug to delete

    Returns:
        Response indicating success and any follow-up suggestions
    """
    use_case = get_delete_epic_use_case()
    response = await use_case.execute(DeleteEpicRequest(slug=slug))

    suggestions = []
    if response.deleted:
        suggestions.append({
            "severity": "info",
            "category": "next_step",
            "message": "Epic deleted successfully",
            "action": "Consider updating any journeys that referenced this epic in their steps",
            "tool": "list_journeys",
            "context": {"deleted_slug": slug},
        })

    return {
        "success": response.deleted,
        "entity": None,
        "suggestions": suggestions,
    }
