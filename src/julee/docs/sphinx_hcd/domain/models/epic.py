"""Epic domain model.

Represents an epic in the HCD documentation system.
Epics are defined via RST directives and group related stories together.
"""

from pydantic import Field, field_validator

from julee.core.entities.entity import Entity

from ...utils import normalize_name


class Epic(Entity):
    """Epic entity.

    An epic represents a collection of related stories that together
    deliver a larger piece of functionality or business value.
    """

    slug: str = Field(description='URL-safe identifier (e.g., "credential-creation")')
    description: str = Field(
        default="", description="Human-readable description of the epic"
    )
    story_refs: tuple[str, ...] = Field(
        default_factory=tuple, description="List of story feature titles in this epic"
    )
    docname: str = Field(
        default="", description="RST document name (for incremental builds)"
    )

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug is not empty."""
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    def with_story(self, story_title: str) -> "Epic":
        """The epic with a story reference added.

        An entity is immutable, so this returns a new epic rather than
        changing this one. A title already present is not added twice.

        Args:
            story_title: Feature title of the story to add
        """
        if story_title in self.story_refs:
            return self
        return self.model_copy(update={"story_refs": (*self.story_refs, story_title)})

    def has_story(self, story_title: str) -> bool:
        """Check if this epic contains a specific story.

        Args:
            story_title: Feature title to check (case-insensitive)

        Returns:
            True if the story is in this epic
        """
        story_normalized = normalize_name(story_title)
        return any(normalize_name(ref) == story_normalized for ref in self.story_refs)

    def get_story_refs_normalized(self) -> list[str]:
        """Get normalized story references.

        Returns:
            List of normalized story titles
        """
        return [normalize_name(ref) for ref in self.story_refs]

    @property
    def display_title(self) -> str:
        """Get formatted title for display."""
        return self.slug.replace("-", " ").title()

    @property
    def story_count(self) -> int:
        """Get number of stories in this epic."""
        return len(self.story_refs)

    @property
    def has_stories(self) -> bool:
        """Check if epic has any stories."""
        return len(self.story_refs) > 0
