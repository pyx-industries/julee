"""Use case for resolving story references.

Finds epics and journeys that reference a specific story.
"""

from pydantic import BaseModel

from ..domain.models.epic import Epic
from ..domain.models.journey import Journey
from ..domain.models.story import Story
from ..utils import normalize_name


def get_epics_for_story(
    story: Story,
    epics: list[Epic],
) -> list[Epic]:
    """Get epics that contain a specific story.

    Args:
        story: Story to find epics for
        epics: All Epic entities to search

    Returns:
        List of Epic entities containing this story, sorted by slug
    """
    story_normalized = normalize_name(story.feature_title)
    matching = []

    for epic in epics:
        if any(normalize_name(ref) == story_normalized for ref in epic.story_refs):
            matching.append(epic)

    return sorted(matching, key=lambda e: e.slug)


def get_journeys_for_story(
    story: Story,
    journeys: list[Journey],
) -> list[Journey]:
    """Get journeys that reference a specific story.

    Args:
        story: Story to find journeys for
        journeys: All Journey entities to search

    Returns:
        List of Journey entities containing this story, sorted by slug
    """
    story_normalized = normalize_name(story.feature_title)
    matching = []

    for journey in journeys:
        story_refs = journey.get_story_refs()
        if any(normalize_name(ref) == story_normalized for ref in story_refs):
            matching.append(journey)

    return sorted(matching, key=lambda j: j.slug)


def get_related_stories(
    story: Story,
    stories: list[Story],
    epics: list[Epic],
) -> list[Story]:
    """Get stories related to a story via shared epics.

    Finds other stories that are in the same epic(s) as the given story.

    Args:
        story: Story to find related stories for
        stories: All Story entities
        epics: All Epic entities

    Returns:
        List of related Story entities (excluding the input story), sorted by feature_title
    """
    # Find epics containing this story
    story_epics = get_epics_for_story(story, epics)

    # Collect all story refs from those epics
    related_refs: set[str] = set()
    for epic in story_epics:
        for ref in epic.story_refs:
            related_refs.add(normalize_name(ref))

    # Remove the original story
    story_normalized = normalize_name(story.feature_title)
    related_refs.discard(story_normalized)

    # Find matching stories
    related = []
    for s in stories:
        if normalize_name(s.feature_title) in related_refs:
            related.append(s)

    return sorted(related, key=lambda s: s.feature_title)


class ResolveStoryReferencesRequest(BaseModel):
    """What a story's references are resolved against."""

    story: Story
    stories: tuple[Story, ...] = ()
    epics: tuple[Epic, ...] = ()
    journeys: tuple[Journey, ...] = ()


class ResolveStoryReferencesResponse(BaseModel):
    """Everything that refers to a story."""

    epics: tuple[Epic, ...] = ()
    journeys: tuple[Journey, ...] = ()
    related_stories: tuple[Story, ...] = ()


class ResolveStoryReferencesUseCase:
    """Resolve every reference to a story at once.

    The directives that document a story need its epics, its journeys and
    the stories it shares an epic with. Resolving them together keeps the
    three answers consistent with one another.
    """

    async def execute(
        self, request: ResolveStoryReferencesRequest
    ) -> ResolveStoryReferencesResponse:
        """Resolve a story's references.

        Args:
            request: The story, and the entities to search

        Returns:
            The epics and journeys referring to the story, and its
            related stories
        """
        return ResolveStoryReferencesResponse(
            epics=tuple(get_epics_for_story(request.story, list(request.epics))),
            journeys=tuple(
                get_journeys_for_story(request.story, list(request.journeys))
            ),
            related_stories=tuple(
                get_related_stories(
                    request.story, list(request.stories), list(request.epics)
                )
            ),
        )
