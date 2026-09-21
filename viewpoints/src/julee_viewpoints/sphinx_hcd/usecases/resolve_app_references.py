"""Use case for resolving app references.

Finds stories, personas, journeys, and epics related to an app.
"""

from pydantic import BaseModel

from ..domain.models.app import App
from ..domain.models.epic import Epic
from ..domain.models.journey import Journey
from ..domain.models.persona import Persona
from ..domain.models.story import Story
from ..utils import normalize_name
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


class ResolveAppReferencesRequest(BaseModel):
    """What an app's references are resolved against."""

    app: App
    stories: tuple[Story, ...] = ()
    epics: tuple[Epic, ...] = ()
    journeys: tuple[Journey, ...] = ()


class ResolveAppReferencesResponse(BaseModel):
    """Everything an app is connected to."""

    stories: tuple[Story, ...] = ()
    personas: tuple[Persona, ...] = ()
    journeys: tuple[Journey, ...] = ()
    epics: tuple[Epic, ...] = ()


class ResolveAppReferencesUseCase:
    """Resolve everything an app is connected to at once.

    An app's page shows its stories, the personas who use it, and the
    journeys and epics those stories belong to. All four are derived from
    the same set of stories, so they are resolved together.
    """

    async def execute(
        self, request: ResolveAppReferencesRequest
    ) -> ResolveAppReferencesResponse:
        """Resolve an app's references.

        Args:
            request: The app, and the entities to search

        Returns:
            The stories, personas, journeys and epics connected to the app
        """
        stories = list(request.stories)
        epics = list(request.epics)
        return ResolveAppReferencesResponse(
            stories=tuple(get_stories_for_app(request.app, stories)),
            personas=tuple(get_personas_for_app(request.app, stories, epics)),
            journeys=tuple(
                get_journeys_for_app(request.app, stories, list(request.journeys))
            ),
            epics=tuple(get_epics_for_app(request.app, stories, epics)),
        )
