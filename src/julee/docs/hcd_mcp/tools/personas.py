"""MCP tools for Persona read operations.

Personas are derived from stories and epics, so they are read-only.
All operations delegate to use-case classes following clean architecture.
Responses include contextual suggestions based on domain semantics.
"""

from ...hcd_api.requests import DerivePersonasRequest, GetPersonaRequest
from ...sphinx_hcd.domain.use_cases.suggestions import compute_persona_suggestions
from ..context import (
    get_derive_personas_use_case,
    get_get_persona_use_case,
    get_suggestion_context,
)


async def list_personas() -> dict:
    """List all personas (derived from stories and epics).

    Returns:
        Response with personas list and aggregate suggestions
    """
    use_case = get_derive_personas_use_case()
    response = await use_case.execute(DerivePersonasRequest())

    # Compute aggregate suggestions
    suggestions = []
    ctx = get_suggestion_context()

    # Check for personas without journeys
    all_journeys = await ctx.get_all_journeys()
    journey_personas = {j.persona_normalized for j in all_journeys}

    personas_without_journeys = [
        p for p in response.personas
        if p.normalized_name not in journey_personas
    ]
    if personas_without_journeys:
        suggestions.append({
            "severity": "suggestion",
            "category": "incomplete",
            "message": f"{len(personas_without_journeys)} personas have no journeys defined",
            "action": "Create journeys describing how these personas accomplish their goals",
            "tool": "create_journey",
            "context": {"personas": [p.name for p in personas_without_journeys[:10]]},
        })

    # Story and app coverage info
    total_stories = sum(len(p.app_slugs) for p in response.personas)
    total_epics = sum(len(p.epic_slugs) for p in response.personas)
    suggestions.append({
        "severity": "info",
        "category": "relationship",
        "message": f"{len(response.personas)} personas across {total_stories} app associations and {total_epics} epic participations",
        "action": "Review persona coverage and journey completeness",
        "tool": "list_journeys",
        "context": {
            "persona_count": len(response.personas),
            "app_associations": total_stories,
            "epic_participations": total_epics,
        },
    })

    return {
        "entities": [p.model_dump() for p in response.personas],
        "count": len(response.personas),
        "suggestions": suggestions,
    }


async def get_persona(name: str) -> dict:
    """Get a persona by name (derived from stories and epics).

    Args:
        name: Persona name (case-insensitive)

    Returns:
        Response with persona data and contextual suggestions
    """
    use_case = get_get_persona_use_case()
    response = await use_case.execute(GetPersonaRequest(name=name))

    if not response.persona:
        return {
            "entity": None,
            "found": False,
            "suggestions": [{
                "severity": "info",
                "category": "missing_reference",
                "message": f"No persona named '{name}' found",
                "action": "Create stories with this persona, or check the spelling",
                "tool": "list_personas",
                "context": {"searched_name": name},
            }],
        }

    # Compute suggestions
    ctx = get_suggestion_context()
    suggestions = await compute_persona_suggestions(response.persona, ctx)

    return {
        "entity": response.persona.model_dump(),
        "found": True,
        "suggestions": suggestions,
    }
