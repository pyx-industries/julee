"""MCP tools for Accelerator CRUD operations.

All operations delegate to use-case classes following clean architecture.
Responses include contextual suggestions based on domain semantics.
"""

from typing import Any

from apps.mcp.shared import ResponseFormat, format_entity, paginate_results
from julee.hcd.domain.use_cases.accelerator import (
    CreateAcceleratorRequest,
    DeleteAcceleratorRequest,
    GetAcceleratorRequest,
    IntegrationReferenceItem,
    ListAcceleratorsRequest,
    UpdateAcceleratorRequest,
)
from julee.hcd.domain.use_cases.suggestions import compute_accelerator_suggestions
from ..context import (
    get_create_accelerator_use_case,
    get_delete_accelerator_use_case,
    get_get_accelerator_use_case,
    get_list_accelerators_use_case,
    get_suggestion_context_service,
    get_update_accelerator_use_case,
)


async def create_accelerator(
    slug: str,
    status: str = "",
    milestone: str | None = None,
    acceptance: str | None = None,
    objective: str = "",
    sources_from: list[dict[str, Any]] | None = None,
    publishes_to: list[dict[str, Any]] | None = None,
    depends_on: list[str] | None = None,
    feeds_into: list[str] | None = None,
) -> dict:
    """Create a new accelerator.

    Args:
        slug: Accelerator slug (URL-safe identifier)
        status: Development status (e.g., "alpha", "production")
        milestone: Target milestone
        acceptance: Acceptance criteria
        objective: Business objective/description
        sources_from: Integration references for data sources
        publishes_to: Integration references for data sinks
        depends_on: Accelerator slugs this depends on
        feeds_into: Accelerator slugs this feeds into

    Returns:
        Response with created accelerator and contextual suggestions
    """
    use_case = get_create_accelerator_use_case()

    # Convert dicts to IntegrationReferenceItem objects
    sources = [IntegrationReferenceItem(**s) for s in (sources_from or [])]
    publishes = [IntegrationReferenceItem(**p) for p in (publishes_to or [])]

    request = CreateAcceleratorRequest(
        slug=slug,
        status=status,
        milestone=milestone,
        acceptance=acceptance,
        objective=objective,
        sources_from=sources,
        publishes_to=publishes,
        depends_on=depends_on or [],
        feeds_into=feeds_into or [],
    )
    response = await use_case.execute(request)

    # Compute suggestions
    ctx = get_suggestion_context_service()
    suggestions = await compute_accelerator_suggestions(response.accelerator, ctx)

    return {
        "success": True,
        "entity": response.accelerator.model_dump(),
        "suggestions": suggestions,
    }


async def get_accelerator(slug: str, format: str = "full") -> dict:
    """Get an accelerator by its slug.

    Args:
        slug: Accelerator slug
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with accelerator data and contextual suggestions
    """
    use_case = get_get_accelerator_use_case()
    response = await use_case.execute(GetAcceleratorRequest(slug=slug))

    if not response.accelerator:
        return {
            "entity": None,
            "found": False,
            "suggestions": [],
        }

    # Compute suggestions
    ctx = get_suggestion_context_service()
    suggestions = await compute_accelerator_suggestions(response.accelerator, ctx)

    return {
        "entity": format_entity(
            response.accelerator.model_dump(),
            ResponseFormat.from_string(format),
            "accelerator",
        ),
        "found": True,
        "suggestions": suggestions,
    }


async def list_accelerators(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all accelerators with pagination.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with paginated accelerators list and aggregate suggestions
    """
    use_case = get_list_accelerators_use_case()
    response = await use_case.execute(ListAcceleratorsRequest())

    # Compute aggregate suggestions (on full dataset before pagination)
    suggestions = []

    # Count accelerators without integrations
    no_integrations = [
        a for a in response.accelerators if not a.sources_from and not a.publishes_to
    ]
    if no_integrations:
        suggestions.append(
            {
                "severity": "suggestion",
                "category": "incomplete",
                "message": f"{len(no_integrations)} accelerators have no integrations defined",
                "action": "Define source and publish integrations for data flow clarity",
                "tool": "update_accelerator",
                "context": {
                    "accelerator_slugs": [a.slug for a in no_integrations[:10]]
                },
            }
        )

    # Integration usage info
    all_integrations = set()
    for a in response.accelerators:
        for ref in a.sources_from:
            all_integrations.add(ref.slug)
        for ref in a.publishes_to:
            all_integrations.add(ref.slug)
    if all_integrations:
        suggestions.append(
            {
                "severity": "info",
                "category": "relationship",
                "message": f"Accelerators reference {len(all_integrations)} integrations",
                "action": "Review integration coverage",
                "tool": "list_integrations",
                "context": {"integration_count": len(all_integrations)},
            }
        )

    # Format entities based on requested verbosity
    fmt = ResponseFormat.from_string(format)
    all_entities = [
        format_entity(a.model_dump(), fmt, "accelerator") for a in response.accelerators
    ]

    # Apply pagination
    result = paginate_results(all_entities, limit=limit, offset=offset)
    result["suggestions"] = suggestions

    return result


async def update_accelerator(
    slug: str,
    status: str | None = None,
    milestone: str | None = None,
    acceptance: str | None = None,
    objective: str | None = None,
    sources_from: list[dict[str, Any]] | None = None,
    publishes_to: list[dict[str, Any]] | None = None,
    depends_on: list[str] | None = None,
    feeds_into: list[str] | None = None,
) -> dict:
    """Update an existing accelerator.

    Args:
        slug: Accelerator slug to update
        status: New status (optional)
        milestone: New milestone (optional)
        acceptance: New acceptance criteria (optional)
        objective: New objective (optional)
        sources_from: New source integrations (optional)
        publishes_to: New publish integrations (optional)
        depends_on: New dependencies (optional)
        feeds_into: New feeds into (optional)

    Returns:
        Response with updated accelerator and contextual suggestions
    """
    use_case = get_update_accelerator_use_case()

    # Convert dicts to IntegrationReferenceItem objects if provided
    sources = None
    if sources_from is not None:
        sources = [IntegrationReferenceItem(**s) for s in sources_from]
    publishes = None
    if publishes_to is not None:
        publishes = [IntegrationReferenceItem(**p) for p in publishes_to]

    request = UpdateAcceleratorRequest(
        slug=slug,
        status=status,
        milestone=milestone,
        acceptance=acceptance,
        objective=objective,
        sources_from=sources,
        publishes_to=publishes,
        depends_on=depends_on,
        feeds_into=feeds_into,
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
        await compute_accelerator_suggestions(response.accelerator, ctx)
        if response.accelerator
        else []
    )

    return {
        "success": True,
        "entity": response.accelerator.model_dump() if response.accelerator else None,
        "suggestions": suggestions,
    }


async def delete_accelerator(slug: str) -> dict:
    """Delete an accelerator by slug.

    Args:
        slug: Accelerator slug to delete

    Returns:
        Response indicating success and any follow-up suggestions
    """
    use_case = get_delete_accelerator_use_case()
    response = await use_case.execute(DeleteAcceleratorRequest(slug=slug))

    suggestions = []
    if response.deleted:
        suggestions.append(
            {
                "severity": "info",
                "category": "next_step",
                "message": "Accelerator deleted successfully",
                "action": "Consider updating apps and other accelerators that referenced this one",
                "tool": "list_apps",
                "context": {"deleted_slug": slug},
            }
        )

    return {
        "success": response.deleted,
        "entity": None,
        "suggestions": suggestions,
    }
