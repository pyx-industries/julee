"""Story domain model.

Represents a user story extracted from a Gherkin .feature file.
"""

from pydantic import BaseModel, field_validator

from julee.hcd.utils import normalize_name, slugify


class Story(BaseModel):
    """A user story extracted from a Gherkin feature file.

    Stories are the primary unit of user-facing functionality in HCD.
    They capture who wants to do what and why.
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

    # Solution scoping
    solution_slug: str = ""

    # Document structure (RST round-trip)
    page_title: str = ""
    preamble_rst: str = ""
    epilogue_rst: str = ""

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
    def from_create_data(
        cls,
        feature_title: str,
        persona: str,
        app_slug: str,
        i_want: str = "do something",
        so_that: str = "achieve a goal",
        file_path: str = "",
        abs_path: str = "",
        gherkin_snippet: str = "",
        **kwargs,
    ) -> "Story":
        """Create a Story from request data (doctrine pattern for generic CRUD).

        Generates slug from app_slug + feature_title. Validates via entity validators.

        Args:
            feature_title: The Feature: line content
            persona: The "As a" actor
            app_slug: Application slug (from directory structure)
            i_want: The "I want to" action
            so_that: The "So that" benefit
            file_path: Relative path to .feature file
            abs_path: Absolute path to .feature file
            gherkin_snippet: The story header text
            **kwargs: Ignored (allows extra fields from request)

        Returns:
            A new Story instance
        """
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
        return cls.from_create_data(
            feature_title=feature_title,
            persona=persona,
            app_slug=app_slug,
            i_want=i_want,
            so_that=so_that,
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
