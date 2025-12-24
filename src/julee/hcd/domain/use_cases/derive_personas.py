"""Use case for deriving personas from stories and epics.

Personas are not defined directly but are extracted from user stories.
This use case collects persona information from stories and enriches
it with epic participation data.
"""

from collections import defaultdict

from julee.hcd.entities.app import App
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.persona import Persona
from julee.hcd.entities.story import Story
from julee.hcd.utils import normalize_name


def derive_personas(
    stories: list[Story],
    epics: list[Epic],
) -> list[Persona]:
    """Derive personas from stories and epics.

    Extracts unique personas from stories, then enriches with:
    - List of apps each persona uses (from stories)
    - List of epics each persona participates in (stories in epics)

    Args:
        stories: List of Story entities
        epics: List of Epic entities

    Returns:
        List of Persona entities sorted by name
    """
    # Collect persona data from stories
    persona_data: dict[str, dict] = {}  # normalized_name -> {name, apps}

    for story in stories:
        normalized = story.persona_normalized
        if normalized == "unknown":
            continue

        if normalized not in persona_data:
            persona_data[normalized] = {
                "name": story.persona,
                "apps": set(),
                "epics": set(),
            }

        persona_data[normalized]["apps"].add(story.app_slug)

    # Build lookup of normalized story title -> normalized persona
    story_to_persona: dict[str, str] = {}
    for story in stories:
        story_to_persona[normalize_name(story.feature_title)] = story.persona_normalized

    # Find epics for each persona
    for epic in epics:
        for story_ref in epic.story_refs:
            story_normalized = normalize_name(story_ref)
            persona_normalized = story_to_persona.get(story_normalized)
            if persona_normalized and persona_normalized in persona_data:
                persona_data[persona_normalized]["epics"].add(epic.slug)

    # Build Persona entities
    personas = []
    for data in persona_data.values():
        persona = Persona(
            name=data["name"],
            app_slugs=sorted(data["apps"]),
            epic_slugs=sorted(data["epics"]),
        )
        personas.append(persona)

    return sorted(personas, key=lambda p: p.name)


def derive_personas_by_app_type(
    stories: list[Story],
    epics: list[Epic],
    apps: list[App],
) -> dict[str, list[Persona]]:
    """Derive personas grouped by the type of apps they use.

    Args:
        stories: List of Story entities
        epics: List of Epic entities
        apps: List of App entities

    Returns:
        Dict mapping app type strings to lists of Persona entities
    """
    # First derive all personas
    all_personas = derive_personas(stories, epics)

    # Build app slug -> app type lookup
    app_types: dict[str, str] = {}
    for app in apps:
        app_types[app.slug] = app.app_type.value if app.app_type else "unknown"

    # Group personas by app type
    personas_by_type: dict[str, list[Persona]] = defaultdict(list)

    for persona in all_personas:
        # Find all app types this persona uses
        persona_types: set[str] = set()
        for app_slug in persona.app_slugs:
            app_type = app_types.get(app_slug, "unknown")
            persona_types.add(app_type)

        # Add persona to each type group
        for app_type in persona_types:
            personas_by_type[app_type].append(persona)

    # Sort personas within each group
    return {
        app_type: sorted(personas, key=lambda p: p.name)
        for app_type, personas in personas_by_type.items()
    }


def get_epics_for_persona(
    persona: Persona,
    epics: list[Epic],
    stories: list[Story],
) -> list[Epic]:
    """Get Epic entities for a persona.

    Args:
        persona: Persona to get epics for
        epics: All Epic entities
        stories: All Story entities

    Returns:
        List of Epic entities containing stories for this persona
    """
    # Build lookup of normalized story title -> normalized persona
    story_to_persona: dict[str, str] = {}
    for story in stories:
        story_to_persona[normalize_name(story.feature_title)] = story.persona_normalized

    matching_epics = []
    for epic in epics:
        for story_ref in epic.story_refs:
            story_normalized = normalize_name(story_ref)
            if story_to_persona.get(story_normalized) == persona.normalized_name:
                matching_epics.append(epic)
                break

    return sorted(matching_epics, key=lambda e: e.slug)


def get_apps_for_persona(
    persona: Persona,
    apps: list[App],
) -> list[App]:
    """Get App entities for a persona.

    Args:
        persona: Persona to get apps for
        apps: All App entities

    Returns:
        List of App entities this persona uses
    """
    app_lookup = {app.slug: app for app in apps}
    return [app_lookup[slug] for slug in persona.app_slugs if slug in app_lookup]
