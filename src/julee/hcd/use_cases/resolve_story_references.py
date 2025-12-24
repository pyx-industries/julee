"""Use case for resolving story references.

Finds epics and journeys that reference a specific story.
"""

from julee.hcd.entities.epic import Epic
from julee.hcd.entities.journey import Journey
from julee.hcd.entities.story import Story
from julee.hcd.utils import normalize_name


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


def get_story_cross_references(
    story: Story,
    stories: list[Story],
    epics: list[Epic],
    journeys: list[Journey],
) -> dict:
    """Get all cross-references for a story.

    Convenience function to get all related entities at once.

    Args:
        story: Story to find references for
        stories: All Story entities
        epics: All Epic entities
        journeys: All Journey entities

    Returns:
        Dict with keys: epics, journeys, related_stories
    """
    return {
        "epics": get_epics_for_story(story, epics),
        "journeys": get_journeys_for_story(story, journeys),
        "related_stories": get_related_stories(story, stories, epics),
    }
