"""Story domain model.

Represents a user story extracted from a Gherkin .feature file.
"""

from pydantic import BaseModel, field_validator

from ...utils import normalize_name, slugify


class Story(BaseModel):
    """A user story extracted from a Gherkin feature file.

    Stories are the primary unit of user-facing functionality in HCD.
    They capture who wants to do what and why.

    Attributes:
        slug: URL-safe identifier derived from feature title
        feature_title: The Feature: line from the Gherkin file
        persona: The actor from "As a <persona>"
        persona_normalized: Lowercase, spaces-normalized persona for matching
        i_want: The action from "I want to <action>"
        so_that: The benefit from "So that <benefit>"
        app_slug: The application this story belongs to
        app_normalized: Lowercase, spaces-normalized app name for matching
        file_path: Relative path to the .feature file
        abs_path: Absolute path to the .feature file
        gherkin_snippet: The story header portion of the feature file
    """

    slug: str
    feature_title: str
    persona: str
    persona_normalized: str = ""
    i_want: str = "do something"
    so_that: str = "achieve a goal"
    app_slug: str
    app_normalized: str = ""
    file_path: str
    abs_path: str = ""
    gherkin_snippet: str = ""

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Ensure slug is not empty."""
        if not v or not v.strip():
            raise ValueError("Story slug cannot be empty")
        return v.strip()

    @field_validator("feature_title")
    @classmethod
    def validate_feature_title(cls, v: str) -> str:
        """Ensure feature title is not empty."""
        if not v or not v.strip():
            raise ValueError("Feature title cannot be empty")
        return v.strip()

    @field_validator("persona")
    @classmethod
    def validate_persona(cls, v: str) -> str:
        """Ensure persona is not empty, default to 'unknown'."""
        if not v or not v.strip():
            return "unknown"
        return v.strip()

    @field_validator("app_slug")
    @classmethod
    def validate_app_slug(cls, v: str) -> str:
        """Ensure app slug is not empty, default to 'unknown'."""
        if not v or not v.strip():
            return "unknown"
        return v.strip()

    def model_post_init(self, __context) -> None:
        """Compute normalized fields after initialization."""
        if not self.persona_normalized:
            self.persona_normalized = normalize_name(self.persona)
        if not self.app_normalized:
            self.app_normalized = normalize_name(self.app_slug)

    @classmethod
    def from_feature_file(
        cls,
        feature_title: str,
        persona: str,
        i_want: str,
        so_that: str,
        app_slug: str,
        file_path: str,
        abs_path: str = "",
        gherkin_snippet: str = "",
    ) -> "Story":
        """Create a Story from parsed feature file data.

        Args:
            feature_title: The Feature: line content
            persona: The "As a" actor
            i_want: The "I want to" action
            so_that: The "So that" benefit
            app_slug: Application slug (from directory structure)
            file_path: Relative path to .feature file
            abs_path: Absolute path to .feature file
            gherkin_snippet: The story header text

        Returns:
            A new Story instance
        """
        # Include app_slug in slug to avoid collisions between apps
        return cls(
            slug=f"{app_slug}--{slugify(feature_title)}",
            feature_title=feature_title,
            persona=persona,
            i_want=i_want,
            so_that=so_that,
            app_slug=app_slug,
            file_path=file_path,
            abs_path=abs_path,
            gherkin_snippet=gherkin_snippet,
        )

    def matches_persona(self, persona_name: str) -> bool:
        """Check if this story belongs to a persona (case-insensitive)."""
        return self.persona_normalized == normalize_name(persona_name)

    def matches_app(self, app_name: str) -> bool:
        """Check if this story belongs to an app (case-insensitive)."""
        return self.app_normalized == normalize_name(app_name)
