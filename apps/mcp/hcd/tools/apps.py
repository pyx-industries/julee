"""MCP tools for App CRUD operations.

All operations delegate to use-case classes following clean architecture.
Responses include contextual suggestions based on domain semantics.
"""

from apps.mcp.shared import ResponseFormat, format_entity, paginate_results
from julee.hcd.use_cases.app import (
    CreateAppRequest,
    DeleteAppRequest,
    GetAppRequest,
    ListAppsRequest,
    UpdateAppRequest,
)
from julee.hcd.use_cases.suggestions import compute_app_suggestions
from ..context import (
    get_create_app_use_case,
    get_delete_app_use_case,
    get_get_app_use_case,
    get_list_apps_use_case,
    get_suggestion_context_service,
    get_update_app_use_case,
)


async def create_app(
    slug: str,
    name: str,
    app_type: str = "unknown",
    status: str | None = None,
    description: str = "",
    accelerators: list[str] | None = None,
) -> dict:
    """Create a new app.

    Args:
        slug: App slug (URL-safe identifier)
        name: Display name
        app_type: App type (staff, external, member-tool, unknown)
        status: Status indicator
        description: App description
        accelerators: List of accelerator slugs

    Returns:
        Response with created app and contextual suggestions
    """
    use_case = get_create_app_use_case()
    request = CreateAppRequest(
        slug=slug,
        name=name,
        app_type=app_type,
        status=status,
        description=description,
        accelerators=accelerators or [],
    )
    response = await use_case.execute(request)

    # Compute suggestions
    ctx = get_suggestion_context_service()
    suggestions = await compute_app_suggestions(response.app, ctx)

    # Add suggestion to create stories
    suggestions.append(
        {
            "severity": "suggestion",
            "category": "next_step",
            "message": "App created - consider adding user stories",
            "action": f"Create user stories that describe what personas can do with '{name}'",
            "tool": "create_story",
            "context": {"app_slug": slug, "app_name": name},
        }
    )

    return {
        "success": True,
        "entity": response.app.model_dump(),
        "suggestions": suggestions,
    }


async def get_app(slug: str, format: str = "full") -> dict:
    """Get an app by its slug.

    Args:
        slug: App slug
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with app data and contextual suggestions
    """
    use_case = get_get_app_use_case()
    response = await use_case.execute(GetAppRequest(slug=slug))

    if not response.app:
        return {
            "entity": None,
            "found": False,
            "suggestions": [],
        }

    # Compute suggestions
    ctx = get_suggestion_context_service()
    suggestions = await compute_app_suggestions(response.app, ctx)

    return {
        "entity": format_entity(
            response.app.model_dump(), ResponseFormat.from_string(format), "app"
        ),
        "found": True,
        "suggestions": suggestions,
    }


async def list_apps(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all apps with pagination.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with paginated apps list and aggregate suggestions
    """
    use_case = get_list_apps_use_case()
    response = await use_case.execute(ListAppsRequest())

    # Compute aggregate suggestions (on full dataset before pagination)
    suggestions = []
    ctx = get_suggestion_context_service()

    # Check for apps without stories
    apps_without_stories = []
    for app in response.apps:
        stories = await ctx.get_stories_for_app(app.slug)
        if not stories:
            apps_without_stories.append(app)

    if apps_without_stories:
        suggestions.append(
            {
                "severity": "suggestion",
                "category": "incomplete",
                "message": f"{len(apps_without_stories)} apps have no user stories",
                "action": "Create stories describing what personas can do with these apps",
                "tool": "create_story",
                "context": {"app_slugs": [a.slug for a in apps_without_stories[:10]]},
            }
        )

    # App type distribution
    app_types = {}
    for app in response.apps:
        type_name = (
            app.app_type.value if hasattr(app.app_type, "value") else str(app.app_type)
        )
        app_types[type_name] = app_types.get(type_name, 0) + 1
    if app_types:
        suggestions.append(
            {
                "severity": "info",
                "category": "relationship",
                "message": f"App types: {app_types}",
                "action": "Review app classification",
                "tool": None,
                "context": {"type_counts": app_types},
            }
        )

    # Format entities based on requested verbosity
    fmt = ResponseFormat.from_string(format)
    all_entities = [format_entity(a.model_dump(), fmt, "app") for a in response.apps]

    # Apply pagination
    result = paginate_results(all_entities, limit=limit, offset=offset)
    result["suggestions"] = suggestions

    return result


async def update_app(
    slug: str,
    name: str | None = None,
    app_type: str | None = None,
    status: str | None = None,
    description: str | None = None,
    accelerators: list[str] | None = None,
) -> dict:
    """Update an existing app.

    Args:
        slug: App slug to update
        name: New name (optional)
        app_type: New app type (optional)
        status: New status (optional)
        description: New description (optional)
        accelerators: New accelerators (optional)

    Returns:
        Response with updated app and contextual suggestions
    """
    use_case = get_update_app_use_case()
    request = UpdateAppRequest(
        slug=slug,
        name=name,
        app_type=app_type,
        status=status,
        description=description,
        accelerators=accelerators,
    )
    response = await use_case.execute(request)

    if not response.found:
        return {
            "success": False,
            "entity": None,
            "suggestions": [],
        }

    # Compute suggestions
    ctx = get_suggestion_context_service()
    suggestions = (
        await compute_app_suggestions(response.app, ctx) if response.app else []
    )

    return {
        "success": True,
        "entity": response.app.model_dump() if response.app else None,
        "suggestions": suggestions,
    }


async def delete_app(slug: str) -> dict:
    """Delete an app by slug.

    Args:
        slug: App slug to delete

    Returns:
        Response indicating success and any follow-up suggestions
    """
    use_case = get_delete_app_use_case()
    response = await use_case.execute(DeleteAppRequest(slug=slug))

    suggestions = []
    if response.deleted:
        suggestions.append(
            {
                "severity": "warning",
                "category": "next_step",
                "message": "App deleted - stories may be orphaned",
                "action": "Review and reassign stories that belonged to this app",
                "tool": "list_stories",
                "context": {"deleted_slug": slug},
            }
        )

    return {
        "success": response.deleted,
        "entity": None,
        "suggestions": suggestions,
    }
