"""MCP tools for Persona CRUD operations.

Personas can be defined explicitly (first-class) or derived from stories and epics.
Defined personas are authoritative; derived personas act as fallback with warnings.
All operations delegate to use-case classes following clean architecture.
Responses include contextual suggestions based on domain semantics.
"""

from ...hcd_api.requests import (
    CreatePersonaRequest,
    DeletePersonaRequest,
    DerivePersonasRequest,
    GetPersonaRequest,
    UpdatePersonaRequest,
)
from ...sphinx_hcd.domain.use_cases.suggestions import compute_persona_suggestions
from ..context import (
    get_create_persona_use_case,
    get_delete_persona_use_case,
    get_derive_personas_use_case,
    get_get_persona_use_case,
    get_suggestion_context,
    get_update_persona_use_case,
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


async def create_persona(
    slug: str,
    name: str,
    goals: list[str] | None = None,
    frustrations: list[str] | None = None,
    jobs_to_be_done: list[str] | None = None,
    context: str = "",
) -> dict:
    """Create a new persona definition.

    Creates a first-class persona that can be referenced by stories.
    This is the top-down approach where personas are defined before stories.

    Args:
        slug: URL-safe identifier (e.g., "solutions-developer")
        name: Human-readable name used in stories (e.g., "Solutions Developer")
        goals: What this persona wants to achieve
        frustrations: Pain points this persona experiences
        jobs_to_be_done: JTBD for this persona
        context: Background information about this persona

    Returns:
        Response with created persona and contextual suggestions
    """
    use_case = get_create_persona_use_case()
    request = CreatePersonaRequest(
        slug=slug,
        name=name,
        goals=goals or [],
        frustrations=frustrations or [],
        jobs_to_be_done=jobs_to_be_done or [],
        context=context,
    )
    response = await use_case.execute(request)

    # Compute suggestions for the new persona
    ctx = get_suggestion_context()
    suggestions = await compute_persona_suggestions(response.persona, ctx)

    return {
        "entity": response.persona.model_dump(),
        "created": True,
        "suggestions": suggestions,
    }


async def update_persona(
    slug: str,
    name: str | None = None,
    goals: list[str] | None = None,
    frustrations: list[str] | None = None,
    jobs_to_be_done: list[str] | None = None,
    context: str | None = None,
) -> dict:
    """Update an existing persona definition.

    Only updates fields that are provided (non-None).

    Args:
        slug: Persona identifier to update
        name: New human-readable name (optional)
        goals: New goals list (optional, replaces existing)
        frustrations: New frustrations list (optional, replaces existing)
        jobs_to_be_done: New JTBD list (optional, replaces existing)
        context: New background context (optional)

    Returns:
        Response with updated persona and contextual suggestions
    """
    use_case = get_update_persona_use_case()
    request = UpdatePersonaRequest(
        slug=slug,
        name=name,
        goals=goals,
        frustrations=frustrations,
        jobs_to_be_done=jobs_to_be_done,
        context=context,
    )
    response = await use_case.execute(request)

    if not response.persona:
        return {
            "entity": None,
            "updated": False,
            "suggestions": [{
                "severity": "warning",
                "category": "missing_reference",
                "message": f"No persona with slug '{slug}' found",
                "action": "Create the persona first or check the slug",
                "tool": "mcp_create_persona",
                "context": {"slug": slug},
            }],
        }

    # Compute suggestions for the updated persona
    ctx = get_suggestion_context()
    suggestions = await compute_persona_suggestions(response.persona, ctx)

    return {
        "entity": response.persona.model_dump(),
        "updated": True,
        "suggestions": suggestions,
    }


async def delete_persona(slug: str) -> dict:
    """Delete a persona definition.

    Note: This only removes the explicit persona definition. Stories
    referencing this persona will continue to work (with derived persona).

    Args:
        slug: Persona identifier to delete

    Returns:
        Response indicating success and any related warnings
    """
    use_case = get_delete_persona_use_case()
    request = DeletePersonaRequest(slug=slug)
    response = await use_case.execute(request)

    if not response.deleted:
        return {
            "deleted": False,
            "suggestions": [{
                "severity": "info",
                "category": "missing_reference",
                "message": f"No persona with slug '{slug}' found",
                "action": "The persona may have already been deleted or never existed",
                "tool": "list_personas",
                "context": {"slug": slug},
            }],
        }

    return {
        "deleted": True,
        "slug": slug,
        "suggestions": [{
            "severity": "info",
            "category": "next_step",
            "message": "Persona definition deleted",
            "action": "Stories referencing this persona will now show reconciliation warnings",
            "tool": "list_stories",
            "context": {"deleted_slug": slug},
        }],
    }
