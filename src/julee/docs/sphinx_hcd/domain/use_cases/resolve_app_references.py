"""Use case for resolving app references.

Finds stories, personas, journeys, and epics related to an app.
"""

from ...utils import normalize_name
from ..models.app import App
from ..models.epic import Epic
from ..models.journey import Journey
from ..models.persona import Persona
from ..models.story import Story
from .derive_personas import derive_personas


def get_stories_for_app(
    app: App,
    stories: list[Story],
) -> list[Story]:
    """Get stories that belong to an app.

    Args:
        app: App to find stories for
        stories: All Story entities

    Returns:
        List of Story entities for this app, sorted by feature_title
    """
    matching = [s for s in stories if s.app_slug == app.slug]
    return sorted(matching, key=lambda s: s.feature_title)


def get_personas_for_app(
    app: App,
    stories: list[Story],
    epics: list[Epic],
) -> list[Persona]:
    """Get personas that use an app.

    Args:
        app: App to find personas for
        stories: All Story entities
        epics: All Epic entities (for persona derivation)

    Returns:
        List of Persona entities that use this app, sorted by name
    """
    # Derive all personas
    all_personas = derive_personas(stories, epics)

    # Filter to those using this app
    matching = [p for p in all_personas if app.slug in p.app_slugs]
    return sorted(matching, key=lambda p: p.name)


def get_journeys_for_app(
    app: App,
    stories: list[Story],
    journeys: list[Journey],
) -> list[Journey]:
    """Get journeys that include stories from an app.

    Args:
        app: App to find journeys for
        stories: All Story entities
        journeys: All Journey entities

    Returns:
        List of Journey entities containing stories from this app, sorted by slug
    """
    # Get story titles for this app
    app_story_titles = {
        normalize_name(s.feature_title) for s in stories if s.app_slug == app.slug
    }

    if not app_story_titles:
        return []

    # Find journeys containing these stories
    matching = []
    for journey in journeys:
        story_refs = journey.get_story_refs()
        if any(normalize_name(ref) in app_story_titles for ref in story_refs):
            matching.append(journey)

    return sorted(matching, key=lambda j: j.slug)


def get_epics_for_app(
    app: App,
    stories: list[Story],
    epics: list[Epic],
) -> list[Epic]:
    """Get epics that contain stories from an app.

    Args:
        app: App to find epics for
        stories: All Story entities
        epics: All Epic entities

    Returns:
        List of Epic entities containing stories from this app, sorted by slug
    """
    # Get story titles for this app
    app_story_titles = {
        normalize_name(s.feature_title) for s in stories if s.app_slug == app.slug
    }

    if not app_story_titles:
        return []

    # Find epics containing these stories
    matching = []
    for epic in epics:
        if any(normalize_name(ref) in app_story_titles for ref in epic.story_refs):
            matching.append(epic)

    return sorted(matching, key=lambda e: e.slug)


def get_app_cross_references(
    app: App,
    stories: list[Story],
    epics: list[Epic],
    journeys: list[Journey],
) -> dict:
    """Get all cross-references for an app.

    Convenience function to get all related entities at once.

    Args:
        app: App to find references for
        stories: All Story entities
        epics: All Epic entities
        journeys: All Journey entities

    Returns:
        Dict with keys: stories, personas, journeys, epics
    """
    return {
        "stories": get_stories_for_app(app, stories),
        "personas": get_personas_for_app(app, stories, epics),
        "journeys": get_journeys_for_app(app, stories, journeys),
        "epics": get_epics_for_app(app, stories, epics),
    }
