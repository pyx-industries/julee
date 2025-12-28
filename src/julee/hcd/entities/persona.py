"""Persona domain model.

Represents a persona in the HCD documentation system.
Personas can be either:
1. Defined explicitly with HCD metadata (goals, frustrations, JTBD)
2. Derived from user stories (the "As a..." in Gherkin)
"""

from typing import Self

from pydantic import BaseModel, Field, computed_field, field_validator

from julee.hcd.utils import normalize_name, slugify


class Persona(BaseModel):
    """Persona entity.

    A persona represents a type of user who interacts with the system.
    Personas can be explicitly defined with rich HCD metadata or derived
    from user stories (the "As a..." in "As a [persona], I want to...").
    """

    slug: str = ""
    name: str
    goals: list[str] = Field(default_factory=list)
    frustrations: list[str] = Field(default_factory=list)
    jobs_to_be_done: list[str] = Field(default_factory=list)
    context: str = ""
    app_slugs: list[str] = Field(default_factory=list)
    accelerator_slugs: list[str] = Field(default_factory=list)
    contrib_slugs: list[str] = Field(default_factory=list)
    epic_slugs: list[str] = Field(default_factory=list)
    docname: str = ""

    # Solution scoping
    solution_slug: str = ""

    # Document structure (RST round-trip)
    page_title: str = ""
    preamble_rst: str = ""
    epilogue_rst: str = ""

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    def model_post_init(self, __context: object) -> None:
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            object.__setattr__(self, "slug", slugify(self.name))

    @classmethod
    def from_definition(
        cls,
        slug: str,
        name: str,
        goals: list[str] | None = None,
        frustrations: list[str] | None = None,
        jobs_to_be_done: list[str] | None = None,
        context: str = "",
        docname: str = "",
    ) -> Self:
        """Create a persona from an explicit definition.

        Factory method for creating personas with full HCD metadata.

        Args:
            slug: URL-safe identifier
            name: Display name
            goals: What the persona wants to achieve
            frustrations: Pain points and problems
            jobs_to_be_done: JTBD framework items
            context: Background and situational context
            docname: RST document where defined

        Returns:
            New Persona instance
        """
        return cls(
            slug=slug,
            name=name,
            goals=goals or [],
            frustrations=frustrations or [],
            jobs_to_be_done=jobs_to_be_done or [],
            context=context,
            docname=docname,
        )

    @classmethod
    def from_story_reference(cls, name: str, app_slug: str = "") -> Self:
        """Create a persona derived from a story reference.

        Factory method for creating personas derived from Gherkin stories.
        These have minimal metadata - just the name from "As a [persona]".

        Args:
            name: Persona name from the story
            app_slug: Optional app slug to associate

        Returns:
            New Persona instance with auto-generated slug
        """
        return cls(
            name=name,
            app_slugs=[app_slug] if app_slug else [],
        )

    @computed_field
    @property
    def normalized_name(self) -> str:
        """Get normalized name for matching."""
        return normalize_name(self.name)

    @property
    def is_defined(self) -> bool:
        """Check if this is an explicitly defined persona (vs derived)."""
        return bool(
            self.goals or self.frustrations or self.jobs_to_be_done or self.context
        )

    @property
    def has_hcd_metadata(self) -> bool:
        """Check if persona has HCD metadata."""
        return self.is_defined

    @property
    def display_name(self) -> str:
        """Get formatted name for display (same as name)."""
        return self.name

    @property
    def app_count(self) -> int:
        """Get number of apps this persona uses."""
        return len(self.app_slugs)

    @property
    def epic_count(self) -> int:
        """Get number of epics this persona participates in."""
        return len(self.epic_slugs)

    @property
    def has_apps(self) -> bool:
        """Check if persona uses any apps."""
        return len(self.app_slugs) > 0

    @property
    def has_epics(self) -> bool:
        """Check if persona participates in any epics."""
        return len(self.epic_slugs) > 0

    def uses_app(self, app_slug: str) -> bool:
        """Check if persona uses a specific app.

        Args:
            app_slug: App slug to check

        Returns:
            True if persona uses this app
        """
        return app_slug in self.app_slugs

    def participates_in_epic(self, epic_slug: str) -> bool:
        """Check if persona participates in a specific epic.

        Args:
            epic_slug: Epic slug to check

        Returns:
            True if persona has stories in this epic
        """
        return epic_slug in self.epic_slugs

    def add_app(self, app_slug: str) -> None:
        """Add an app to this persona's app list.

        Args:
            app_slug: App slug to add (duplicates ignored)
        """
        if app_slug not in self.app_slugs:
            self.app_slugs.append(app_slug)

    def add_epic(self, epic_slug: str) -> None:
        """Add an epic to this persona's epic list.

        Args:
            epic_slug: Epic slug to add (duplicates ignored)
        """
        if epic_slug not in self.epic_slugs:
            self.epic_slugs.append(epic_slug)
