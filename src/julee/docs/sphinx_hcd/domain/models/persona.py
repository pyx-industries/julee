"""Persona domain model.

Represents a persona in the HCD documentation system. Personas can be:
- Defined: Explicitly created via define-persona directive with rich metadata
- Derived: Extracted from user stories (backward compatibility)

Defined personas are authoritative. Derived personas act as fallback and
generate reconciliation warnings.
"""

from pydantic import BaseModel, Field, computed_field, field_validator

from ...utils import normalize_name


class Persona(BaseModel):
    """Persona entity.

    A persona represents a type of user who interacts with the system.
    Personas can be defined explicitly (with goals, frustrations, etc.) or
    derived from user stories (the "As a..." in "As a [persona], I want to...").

    Attributes:
        slug: URL-safe identifier (empty for derived personas)
        name: Display name of the persona (e.g., "Solutions Developer")
        goals: What the persona wants to achieve
        frustrations: Pain points and problems they face
        jobs_to_be_done: Functional/emotional/social jobs (JTBD framework)
        context: Background and situational context
        docname: RST document where defined (empty for derived personas)
        app_slugs: List of app slugs this persona uses (enriched from stories)
        epic_slugs: List of epic slugs containing stories for this persona
    """

    slug: str = ""
    name: str
    goals: list[str] = Field(default_factory=list)
    frustrations: list[str] = Field(default_factory=list)
    jobs_to_be_done: list[str] = Field(default_factory=list)
    context: str = ""
    docname: str = ""
    app_slugs: list[str] = Field(default_factory=list)
    epic_slugs: list[str] = Field(default_factory=list)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @computed_field
    @property
    def normalized_name(self) -> str:
        """Get normalized name for matching."""
        return normalize_name(self.name)

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

    @property
    def is_defined(self) -> bool:
        """Check if this persona was explicitly defined (vs derived from stories).

        Returns:
            True if persona was defined via define-persona directive
        """
        return bool(self.docname)

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
    ) -> "Persona":
        """Create a defined persona from directive data.

        Args:
            slug: URL-safe identifier
            name: Display name (used in Gherkin "As a {name}")
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

    def merge_with_derived(self, derived: "Persona") -> "Persona":
        """Merge this defined persona with derived data from stories.

        Enriches the defined persona with app_slugs and epic_slugs from
        story analysis. The defined persona's metadata (goals, frustrations,
        etc.) is preserved.

        Args:
            derived: Persona derived from stories with same normalized name

        Returns:
            New Persona with merged data
        """
        # Combine app and epic slugs, removing duplicates
        merged_apps = list(set(self.app_slugs + derived.app_slugs))
        merged_epics = list(set(self.epic_slugs + derived.epic_slugs))

        return Persona(
            slug=self.slug,
            name=self.name,
            goals=self.goals,
            frustrations=self.frustrations,
            jobs_to_be_done=self.jobs_to_be_done,
            context=self.context,
            docname=self.docname,
            app_slugs=sorted(merged_apps),
            epic_slugs=sorted(merged_epics),
        )
