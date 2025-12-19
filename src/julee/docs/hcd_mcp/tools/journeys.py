"""MCP tools for Journey CRUD operations.

All operations delegate to use-case classes following clean architecture.
Responses include contextual suggestions based on domain semantics.
"""

from typing import Any

from ...hcd_api.requests import (
    CreateJourneyRequest,
    DeleteJourneyRequest,
    GetJourneyRequest,
    JourneyStepInput,
    ListJourneysRequest,
    UpdateJourneyRequest,
)
from ...sphinx_hcd.domain.use_cases.suggestions import compute_journey_suggestions
from ..context import (
    get_create_journey_use_case,
    get_delete_journey_use_case,
    get_get_journey_use_case,
    get_list_journeys_use_case,
    get_suggestion_context,
    get_update_journey_use_case,
)


async def create_journey(
    slug: str,
    persona: str,
    intent: str = "",
    outcome: str = "",
    goal: str = "",
    depends_on: list[str] | None = None,
    steps: list[dict[str, Any]] | None = None,
    preconditions: list[str] | None = None,
    postconditions: list[str] | None = None,
) -> dict:
    """Create a new journey.

    Args:
        slug: Journey slug (URL-safe identifier)
        persona: Persona undertaking the journey
        intent: What the persona wants (motivation)
        outcome: What success looks like (business value)
        goal: Activity description
        depends_on: List of journey slugs this depends on
        steps: List of journey steps (dicts with step_type and ref)
        preconditions: List of preconditions
        postconditions: List of postconditions

    Returns:
        Response with created journey and contextual suggestions
    """
    use_case = get_create_journey_use_case()

    # Convert step dicts to JourneyStepInput objects
    step_inputs = []
    if steps:
        for step in steps:
            step_inputs.append(JourneyStepInput(**step))

    request = CreateJourneyRequest(
        slug=slug,
        persona=persona,
        intent=intent,
        outcome=outcome,
        goal=goal,
        depends_on=depends_on or [],
        steps=step_inputs,
        preconditions=preconditions or [],
        postconditions=postconditions or [],
    )
    response = await use_case.execute(request)

    # Compute suggestions
    ctx = get_suggestion_context()
    suggestions = await compute_journey_suggestions(response.journey, ctx)

    return {
        "success": True,
        "entity": response.journey.model_dump(),
        "suggestions": suggestions,
    }


async def get_journey(slug: str) -> dict:
    """Get a journey by its slug.

    Args:
        slug: Journey slug

    Returns:
        Response with journey data and contextual suggestions
    """
    use_case = get_get_journey_use_case()
    response = await use_case.execute(GetJourneyRequest(slug=slug))

    if not response.journey:
        return {
            "entity": None,
            "found": False,
            "suggestions": [],
        }

    # Compute suggestions
    ctx = get_suggestion_context()
    suggestions = await compute_journey_suggestions(response.journey, ctx)

    return {
        "entity": response.journey.model_dump(),
        "found": True,
        "suggestions": suggestions,
    }


async def list_journeys() -> dict:
    """List all journeys.

    Returns:
        Response with journeys list and aggregate suggestions
    """
    use_case = get_list_journeys_use_case()
    response = await use_case.execute(ListJourneysRequest())

    # Compute aggregate suggestions
    suggestions = []

    # Count journeys without steps
    empty_journeys = [j for j in response.journeys if not j.steps]
    if empty_journeys:
        suggestions.append({
            "severity": "warning",
            "category": "incomplete",
            "message": f"{len(empty_journeys)} journeys have no steps defined",
            "action": "Define the sequence of steps for these journeys",
            "tool": "update_journey",
            "context": {"empty_journey_slugs": [j.slug for j in empty_journeys[:10]]},
        })

    # Persona coverage info
    personas = {}
    for j in response.journeys:
        if j.persona:
            personas[j.persona] = personas.get(j.persona, 0) + 1
    if personas:
        suggestions.append({
            "severity": "info",
            "category": "relationship",
            "message": f"Journeys cover {len(personas)} personas",
            "action": "Review persona coverage across journeys",
            "tool": "list_personas",
            "context": {"personas": dict(sorted(personas.items(), key=lambda x: -x[1])[:10])},
        })

    return {
        "entities": [j.model_dump() for j in response.journeys],
        "count": len(response.journeys),
        "suggestions": suggestions,
    }


async def update_journey(
    slug: str,
    persona: str | None = None,
    intent: str | None = None,
    outcome: str | None = None,
    goal: str | None = None,
    depends_on: list[str] | None = None,
    steps: list[dict[str, Any]] | None = None,
    preconditions: list[str] | None = None,
    postconditions: list[str] | None = None,
) -> dict:
    """Update an existing journey.

    Args:
        slug: Journey slug to update
        persona: New persona (optional)
        intent: New intent (optional)
        outcome: New outcome (optional)
        goal: New goal (optional)
        depends_on: New dependencies (optional)
        steps: New steps (optional)
        preconditions: New preconditions (optional)
        postconditions: New postconditions (optional)

    Returns:
        Response with updated journey and contextual suggestions
    """
    use_case = get_update_journey_use_case()

    # Convert step dicts to JourneyStepInput objects if provided
    step_inputs = None
    if steps is not None:
        step_inputs = [JourneyStepInput(**s) for s in steps]

    request = UpdateJourneyRequest(
        slug=slug,
        persona=persona,
        intent=intent,
        outcome=outcome,
        goal=goal,
        depends_on=depends_on,
        steps=step_inputs,
        preconditions=preconditions,
        postconditions=postconditions,
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
    suggestions = await compute_journey_suggestions(response.journey, ctx) if response.journey else []

    return {
        "success": True,
        "entity": response.journey.model_dump() if response.journey else None,
        "suggestions": suggestions,
    }


async def delete_journey(slug: str) -> dict:
    """Delete a journey by slug.

    Args:
        slug: Journey slug to delete

    Returns:
        Response indicating success and any follow-up suggestions
    """
    use_case = get_delete_journey_use_case()
    response = await use_case.execute(DeleteJourneyRequest(slug=slug))

    suggestions = []
    if response.deleted:
        suggestions.append({
            "severity": "info",
            "category": "next_step",
            "message": "Journey deleted successfully",
            "action": "Consider updating any journeys that depended on this one",
            "tool": "list_journeys",
            "context": {"deleted_slug": slug},
        })

    return {
        "success": response.deleted,
        "entity": None,
        "suggestions": suggestions,
    }
