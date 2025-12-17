"""Persona domain model.

Represents a persona derived from story data in the HCD documentation system.
Personas are not defined directly but are extracted from user stories.
"""

from pydantic import BaseModel, Field, computed_field, field_validator

from ...utils import normalize_name


class Persona(BaseModel):
    """Persona entity.

    A persona represents a type of user who interacts with the system.
    Personas are derived from user stories - they are the "As a..." in
    "As a [persona], I want to...".

    Attributes:
        name: Display name of the persona (e.g., "Knowledge Curator")
        app_slugs: List of app slugs this persona uses
        epic_slugs: List of epic slugs containing stories for this persona
    """

    name: str
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
