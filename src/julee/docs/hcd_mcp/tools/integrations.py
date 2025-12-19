"""MCP tools for Integration CRUD operations.

All operations delegate to use-case classes following clean architecture.
Responses include contextual suggestions based on domain semantics.
"""

from typing import Any

from ...hcd_api.requests import (
    CreateIntegrationRequest,
    DeleteIntegrationRequest,
    ExternalDependencyInput,
    GetIntegrationRequest,
    ListIntegrationsRequest,
    UpdateIntegrationRequest,
)
from ...mcp_shared import ResponseFormat, format_entity, paginate_results
from ...sphinx_hcd.domain.use_cases.suggestions import compute_integration_suggestions
from ..context import (
    get_create_integration_use_case,
    get_delete_integration_use_case,
    get_get_integration_use_case,
    get_list_integrations_use_case,
    get_suggestion_context,
    get_update_integration_use_case,
)


async def create_integration(
    slug: str,
    module: str,
    name: str,
    description: str = "",
    direction: str = "bidirectional",
    depends_on: list[dict[str, Any]] | None = None,
) -> dict:
    """Create a new integration.

    Args:
        slug: Integration slug (URL-safe identifier)
        module: Python module name
        name: Display name
        description: Integration description
        direction: Data flow direction (inbound, outbound, bidirectional)
        depends_on: External dependencies (list of dicts with name, url, description)

    Returns:
        Response with created integration and contextual suggestions
    """
    use_case = get_create_integration_use_case()

    # Convert dicts to ExternalDependencyInput objects
    deps = [ExternalDependencyInput(**d) for d in (depends_on or [])]

    request = CreateIntegrationRequest(
        slug=slug,
        module=module,
        name=name,
        description=description,
        direction=direction,
        depends_on=deps,
    )
    response = await use_case.execute(request)

    # Compute suggestions
    ctx = get_suggestion_context()
    suggestions = await compute_integration_suggestions(response.integration, ctx)

    # Add suggestion to connect to accelerators
    suggestions.append(
        {
            "severity": "suggestion",
            "category": "next_step",
            "message": "Integration created - consider connecting it to accelerators",
            "action": "Add this integration to an accelerator's sources_from or publishes_to",
            "tool": "update_accelerator",
            "context": {"integration_slug": slug},
        }
    )

    return {
        "success": True,
        "entity": response.integration.model_dump(),
        "suggestions": suggestions,
    }


async def get_integration(slug: str, format: str = "full") -> dict:
    """Get an integration by its slug.

    Args:
        slug: Integration slug
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with integration data and contextual suggestions
    """
    use_case = get_get_integration_use_case()
    response = await use_case.execute(GetIntegrationRequest(slug=slug))

    if not response.integration:
        return {
            "entity": None,
            "found": False,
            "suggestions": [],
        }

    # Compute suggestions
    ctx = get_suggestion_context()
    suggestions = await compute_integration_suggestions(response.integration, ctx)

    return {
        "entity": format_entity(
            response.integration.model_dump(),
            ResponseFormat.from_string(format),
            "integration",
        ),
        "found": True,
        "suggestions": suggestions,
    }


async def list_integrations(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all integrations with pagination.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with paginated integrations list and aggregate suggestions
    """
    use_case = get_list_integrations_use_case()
    response = await use_case.execute(ListIntegrationsRequest())

    # Compute aggregate suggestions (on full dataset before pagination)
    suggestions = []

    # Get accelerators to check usage
    ctx = get_suggestion_context()
    all_accelerators = await ctx.get_all_accelerators()

    # Find used integrations
    used_integrations = set()
    for a in all_accelerators:
        for ref in a.sources_from:
            used_integrations.add(ref.slug)
        for ref in a.publishes_to:
            used_integrations.add(ref.slug)

    # Find unused integrations
    unused = [i for i in response.integrations if i.slug not in used_integrations]
    if unused:
        suggestions.append(
            {
                "severity": "info",
                "category": "orphan",
                "message": f"{len(unused)} integrations are not referenced by any accelerators",
                "action": "Consider connecting these integrations to accelerators",
                "tool": "update_accelerator",
                "context": {"unused_integrations": [i.slug for i in unused[:10]]},
            }
        )

    # Direction distribution
    directions = {}
    for i in response.integrations:
        dir_name = (
            i.direction.value if hasattr(i.direction, "value") else str(i.direction)
        )
        directions[dir_name] = directions.get(dir_name, 0) + 1
    if directions:
        suggestions.append(
            {
                "severity": "info",
                "category": "relationship",
                "message": f"Integration directions: {directions}",
                "action": "Review data flow patterns",
                "tool": None,
                "context": {"direction_counts": directions},
            }
        )

    # Format entities based on requested verbosity
    fmt = ResponseFormat.from_string(format)
    all_entities = [
        format_entity(i.model_dump(), fmt, "integration") for i in response.integrations
    ]

    # Apply pagination
    result = paginate_results(all_entities, limit=limit, offset=offset)
    result["suggestions"] = suggestions

    return result


async def update_integration(
    slug: str,
    name: str | None = None,
    description: str | None = None,
    direction: str | None = None,
    depends_on: list[dict[str, Any]] | None = None,
) -> dict:
    """Update an existing integration.

    Args:
        slug: Integration slug to update
        name: New name (optional)
        description: New description (optional)
        direction: New direction (optional)
        depends_on: New dependencies (optional)

    Returns:
        Response with updated integration and contextual suggestions
    """
    use_case = get_update_integration_use_case()

    # Convert dicts to ExternalDependencyInput objects if provided
    deps = None
    if depends_on is not None:
        deps = [ExternalDependencyInput(**d) for d in depends_on]

    request = UpdateIntegrationRequest(
        slug=slug,
        name=name,
        description=description,
        direction=direction,
        depends_on=deps,
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
    suggestions = (
        await compute_integration_suggestions(response.integration, ctx)
        if response.integration
        else []
    )

    return {
        "success": True,
        "entity": response.integration.model_dump() if response.integration else None,
        "suggestions": suggestions,
    }


async def delete_integration(slug: str) -> dict:
    """Delete an integration by slug.

    Args:
        slug: Integration slug to delete

    Returns:
        Response indicating success and any follow-up suggestions
    """
    use_case = get_delete_integration_use_case()
    response = await use_case.execute(DeleteIntegrationRequest(slug=slug))

    suggestions = []
    if response.deleted:
        suggestions.append(
            {
                "severity": "warning",
                "category": "next_step",
                "message": "Integration deleted - accelerators may have broken references",
                "action": "Review and update accelerators that referenced this integration",
                "tool": "list_accelerators",
                "context": {"deleted_slug": slug},
            }
        )

    return {
        "success": response.deleted,
        "entity": None,
        "suggestions": suggestions,
    }
