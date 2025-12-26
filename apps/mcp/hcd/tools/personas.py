"""MCP tools for Persona read operations.

Personas are derived from stories and epics, so they are read-only.
All operations delegate to use-case classes following clean architecture.
Responses include contextual suggestions based on domain semantics.
"""

from apps.mcp.shared import ResponseFormat, format_entity, paginate_results
from julee.hcd.use_cases.queries import DerivePersonasRequest, GetPersonaRequest
from julee.hcd.use_cases.suggestions import compute_persona_suggestions
from ..context import (
    get_derive_personas_use_case,
    get_get_persona_use_case,
    get_suggestion_repositories,
)


async def list_personas(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all personas (derived from stories and epics) with pagination.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with paginated personas list and aggregate suggestions
    """
    use_case = get_derive_personas_use_case()
    response = await use_case.execute(DerivePersonasRequest())

    # Compute aggregate suggestions (on full dataset before pagination)
    suggestions = []
    repos = get_suggestion_repositories()

    # Check for personas without journeys
    all_journeys = await repos.journeys.list_all()
    journey_personas = {j.persona_normalized for j in all_journeys}

    personas_without_journeys = [
        p for p in response.personas if p.normalized_name not in journey_personas
    ]
    if personas_without_journeys:
        suggestions.append(
            {
                "severity": "suggestion",
                "category": "incomplete",
                "message": f"{len(personas_without_journeys)} personas have no journeys defined",
                "action": "Create journeys describing how these personas accomplish their goals",
                "tool": "create_journey",
                "context": {
                    "personas": [p.name for p in personas_without_journeys[:10]]
                },
            }
        )

    # Story and app coverage info
    total_stories = sum(len(p.app_slugs) for p in response.personas)
    total_epics = sum(len(p.epic_slugs) for p in response.personas)
    suggestions.append(
        {
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
        }
    )

    # Format entities based on requested verbosity
    fmt = ResponseFormat.from_string(format)
    all_entities = [
        format_entity(p.model_dump(), fmt, "persona") for p in response.personas
    ]

    # Apply pagination
    result = paginate_results(all_entities, limit=limit, offset=offset)
    result["suggestions"] = suggestions

    return result


async def get_persona(name: str, format: str = "full") -> dict:
    """Get a persona by name (derived from stories and epics).

    Args:
        name: Persona name (case-insensitive)
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with persona data and contextual suggestions
    """
    use_case = get_get_persona_use_case()
    response = await use_case.execute(GetPersonaRequest(name=name))

    if not response.persona:
        return {
            "entity": None,
            "found": False,
            "suggestions": [
                {
                    "severity": "info",
                    "category": "missing_reference",
                    "message": f"No persona named '{name}' found",
                    "action": "Create stories with this persona, or check the spelling",
                    "tool": "list_personas",
                    "context": {"searched_name": name},
                }
            ],
        }

    # Compute suggestions
    repos = get_suggestion_repositories()
    suggestions = await compute_persona_suggestions(response.persona, repos)

    return {
        "entity": format_entity(
            response.persona.model_dump(),
            ResponseFormat.from_string(format),
            "persona",
        ),
        "found": True,
        "suggestions": suggestions,
    }
