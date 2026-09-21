"""Accelerator domain model.

Represents an accelerator (bounded context) in the HCD documentation system.
Accelerators are defined via RST directives and may have associated code.
"""

from pydantic import BaseModel, Field, field_validator


class IntegrationReference(BaseModel):
    """Reference to an integration with optional description.

    Used for sources_from and publishes_to relationships where
    an accelerator may specify what data it sources or publishes.
    """

    slug: str = Field(description='URL-safe identifier (e.g., "vocabulary")')
    description: str = Field(
        default="",
        description='What is sourced/published (e.g., "Scheme documentation")',
    )

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug is not empty."""
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @classmethod
    def from_dict(cls, data: dict | str) -> "IntegrationReference":
        """Create from dict or string.

        Args:
            data: Either a dict with slug/description or a plain string slug

        Returns:
            IntegrationReference instance
        """
        if isinstance(data, str):
            return cls(slug=data)
        return cls(slug=data.get("slug", ""), description=data.get("description", ""))


class Accelerator(BaseModel):
    """Accelerator entity.

    An accelerator represents a bounded context that provides business
    capabilities. It may have associated code in src/{slug}/ and is
    exposed through one or more applications.
    """

    slug: str = Field(description='URL-safe identifier (e.g., "vocabulary")')
    status: str = Field(
        default="",
        description='Development status (e.g., "alpha", "production", "future")',
    )
    milestone: str | None = Field(
        default=None, description='Target milestone (e.g., "2 (Nov 2025)")'
    )
    acceptance: str | None = Field(
        default=None, description="Acceptance criteria description"
    )
    objective: str = Field(default="", description="Business objective/description")
    sources_from: list[IntegrationReference] = Field(
        default_factory=list, description="Integrations this accelerator reads from"
    )
    feeds_into: list[str] = Field(
        default_factory=list, description="Other accelerators this one feeds data into"
    )
    publishes_to: list[IntegrationReference] = Field(
        default_factory=list, description="Integrations this accelerator writes to"
    )
    depends_on: list[str] = Field(
        default_factory=list, description="Other accelerators this one depends on"
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

    @property
    def display_title(self) -> str:
        """Get formatted title for display."""
        return self.slug.replace("-", " ").title()

    @property
    def status_normalized(self) -> str:
        """Get normalized status for grouping."""
        return self.status.lower().strip() if self.status else ""

    def has_integration_dependency(self, integration_slug: str) -> bool:
        """Check if accelerator depends on an integration.

        Args:
            integration_slug: Integration slug to check

        Returns:
            True if sources_from or publishes_to contains this integration
        """
        for ref in self.sources_from:
            if ref.slug == integration_slug:
                return True
        for ref in self.publishes_to:
            if ref.slug == integration_slug:
                return True
        return False

    def has_accelerator_dependency(self, accelerator_slug: str) -> bool:
        """Check if accelerator depends on another accelerator.

        Args:
            accelerator_slug: Accelerator slug to check

        Returns:
            True if depends_on or feeds_into contains this accelerator
        """
        return (
            accelerator_slug in self.depends_on or accelerator_slug in self.feeds_into
        )

    def get_sources_from_slugs(self) -> list[str]:
        """Get list of integration slugs this accelerator sources from."""
        return [ref.slug for ref in self.sources_from]

    def get_publishes_to_slugs(self) -> list[str]:
        """Get list of integration slugs this accelerator publishes to."""
        return [ref.slug for ref in self.publishes_to]

    def get_integration_description(
        self, integration_slug: str, relationship: str
    ) -> str | None:
        """Get description for an integration relationship.

        Args:
            integration_slug: Integration to look up
            relationship: Either "sources_from" or "publishes_to"

        Returns:
            Description if found, None otherwise
        """
        refs = (
            self.sources_from if relationship == "sources_from" else self.publishes_to
        )
        for ref in refs:
            if ref.slug == integration_slug:
                return ref.description or None
        return None
