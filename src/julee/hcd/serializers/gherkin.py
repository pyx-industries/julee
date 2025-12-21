"""Gherkin feature file serializer.

Serializes Story domain objects to Gherkin .feature file format.
"""

from ..domain.models.story import Story


def serialize_story(story: Story) -> str:
    """Serialize a Story to Gherkin .feature format.

    Produces the standard Gherkin user story header format:
        Feature: <feature_title>
          As a <persona>
          I want to <i_want>
          So that <so_that>

    Args:
        story: Story domain object to serialize

    Returns:
        Gherkin feature file content as string
    """
    lines = [
        f"Feature: {story.feature_title}",
        f"  As a {story.persona}",
        f"  I want to {story.i_want}",
        f"  So that {story.so_that}",
    ]
    return "\n".join(lines) + "\n"


def get_story_filename(story: Story) -> str:
    """Get the filename for a story's .feature file.

    Args:
        story: Story domain object

    Returns:
        Filename with .feature extension
    """
    # Use slug without the app prefix for the filename
    # Slug format is: {app_slug}--{feature_slug}
    if "--" in story.slug:
        feature_slug = story.slug.split("--", 1)[1]
    else:
        feature_slug = story.slug
    return f"{feature_slug}.feature"
