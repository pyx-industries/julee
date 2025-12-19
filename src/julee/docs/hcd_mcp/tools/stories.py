"""MCP tools for Story CRUD operations.

All operations delegate to use-case classes following clean architecture.
Responses include contextual suggestions based on domain semantics.
"""

from ...hcd_api.requests import (
    CreateStoryRequest,
    DeleteStoryRequest,
    GetStoryRequest,
    ListStoriesRequest,
    UpdateStoryRequest,
)
from ...mcp_shared import (
    ResponseFormat,
    format_entity,
    not_found_error,
    paginate_results,
)
from ...sphinx_hcd.domain.use_cases.suggestions import compute_story_suggestions
from ..context import (
    get_create_story_use_case,
    get_delete_story_use_case,
    get_get_story_use_case,
    get_list_stories_use_case,
    get_suggestion_context,
    get_update_story_use_case,
)


async def create_story(
    feature_title: str,
    persona: str,
    app_slug: str,
    i_want: str = "do something",
    so_that: str = "achieve a goal",
) -> dict:
    """Create a new user story.

    Args:
        feature_title: Feature title (the main story name)
        persona: The persona (As a <persona>)
        app_slug: Application slug this story belongs to
        i_want: What the persona wants to do (I want to <action>)
        so_that: The benefit (So that <benefit>)

    Returns:
        Response with created story and contextual suggestions
    """
    use_case = get_create_story_use_case()
    request = CreateStoryRequest(
        feature_title=feature_title,
        persona=persona,
        app_slug=app_slug,
        i_want=i_want,
        so_that=so_that,
    )
    response = await use_case.execute(request)

    # Compute suggestions for the created story
    ctx = get_suggestion_context()
    suggestions = await compute_story_suggestions(response.story, ctx)

    return {
        "success": True,
        "entity": response.story.model_dump(),
        "suggestions": suggestions,
    }


async def get_story(slug: str, format: str = "full") -> dict:
    """Get a story by its slug.

    Args:
        slug: Story slug (format: app_slug--feature_slug)
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with story data and contextual suggestions
    """
    use_case = get_get_story_use_case()
    response = await use_case.execute(GetStoryRequest(slug=slug))

    if not response.story:
        # Get available slugs for similar suggestions
        list_use_case = get_list_stories_use_case()
        list_response = await list_use_case.execute(ListStoriesRequest())
        available_slugs = [s.slug for s in list_response.stories]
        return not_found_error("story", slug, available_slugs)

    # Compute suggestions
    ctx = get_suggestion_context()
    suggestions = await compute_story_suggestions(response.story, ctx)

    return {
        "entity": format_entity(
            response.story.model_dump(), ResponseFormat.from_string(format), "story"
        ),
        "found": True,
        "suggestions": suggestions,
    }


async def list_stories(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all stories with pagination.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with paginated stories list and aggregate suggestions
    """
    use_case = get_list_stories_use_case()
    response = await use_case.execute(ListStoriesRequest())

    # Compute aggregate suggestions (on full dataset before pagination)
    suggestions = []

    # Count stories with unknown persona
    unknown_persona_count = sum(
        1 for s in response.stories if s.persona_normalized == "unknown"
    )
    if unknown_persona_count > 0:
        suggestions.append(
            {
                "severity": "warning",
                "category": "incomplete",
                "message": f"{unknown_persona_count} stories have unknown personas",
                "action": "Review and update stories to specify personas in 'As a <persona>' format",
                "tool": "update_story",
                "context": {"count": unknown_persona_count},
            }
        )

    # Persona distribution info
    personas = {}
    for s in response.stories:
        if s.persona_normalized != "unknown":
            personas[s.persona] = personas.get(s.persona, 0) + 1
    if personas:
        suggestions.append(
            {
                "severity": "info",
                "category": "relationship",
                "message": f"Stories span {len(personas)} personas",
                "action": "Consider creating journeys for each persona",
                "tool": "create_journey",
                "context": {
                    "personas": dict(sorted(personas.items(), key=lambda x: -x[1])[:10])
                },
            }
        )

    # Format entities based on requested verbosity
    fmt = ResponseFormat.from_string(format)
    all_entities = [
        format_entity(s.model_dump(), fmt, "story") for s in response.stories
    ]

    # Apply pagination
    result = paginate_results(all_entities, limit=limit, offset=offset)
    result["suggestions"] = suggestions

    return result


async def update_story(
    slug: str,
    feature_title: str | None = None,
    persona: str | None = None,
    i_want: str | None = None,
    so_that: str | None = None,
) -> dict:
    """Update an existing story.

    Args:
        slug: Story slug to update
        feature_title: New feature title (optional)
        persona: New persona (optional)
        i_want: New i_want text (optional)
        so_that: New so_that text (optional)

    Returns:
        Response with updated story and contextual suggestions
    """
    use_case = get_update_story_use_case()
    request = UpdateStoryRequest(
        slug=slug,
        feature_title=feature_title,
        persona=persona,
        i_want=i_want,
        so_that=so_that,
    )
    response = await use_case.execute(request)

    if not response.found:
        # Get available slugs for similar suggestions
        list_use_case = get_list_stories_use_case()
        list_response = await list_use_case.execute(ListStoriesRequest())
        available_slugs = [s.slug for s in list_response.stories]
        error_response = not_found_error("story", slug, available_slugs)
        return {
            "success": False,
            "entity": None,
            "error": error_response.get("error"),
            "suggestions": error_response.get("suggestions", []),
        }

    # Compute suggestions
    ctx = get_suggestion_context()
    suggestions = (
        await compute_story_suggestions(response.story, ctx) if response.story else []
    )

    return {
        "success": True,
        "entity": response.story.model_dump() if response.story else None,
        "suggestions": suggestions,
    }


async def delete_story(slug: str) -> dict:
    """Delete a story by slug.

    Args:
        slug: Story slug to delete

    Returns:
        Response indicating success and any follow-up suggestions
    """
    use_case = get_delete_story_use_case()
    response = await use_case.execute(DeleteStoryRequest(slug=slug))

    suggestions = []
    if response.deleted:
        suggestions.append(
            {
                "severity": "info",
                "category": "next_step",
                "message": "Story deleted successfully",
                "action": "Consider updating any epics that referenced this story",
                "tool": "list_epics",
                "context": {"deleted_slug": slug},
            }
        )

    return {
        "success": response.deleted,
        "entity": None,
        "suggestions": suggestions,
    }
