"""Accelerator: a bounded context, seen as something a solution delivers.

An accelerator is a collection of pipelines that make an area of business
go faster (ADR 001). It is the same thing a bounded context is, named for
what it does for the business rather than for how the code is arranged,
and it is how both documentation and supply-chain provenance refer to a
solution's parts.

It lives in the kernel because two kits that cannot see each other need
the same definition: the public documentation kits, and the private
supply-chain one. Neither can own it without the other depending on it.
"""

from pydantic import Field, field_validator

from julee.core.entities.entity import Entity


class AcceleratorValidationIssue(Entity):
    """Something wrong with one accelerator, found by comparing it to code.

    Validation reads what the documentation claims and what the code
    contains, and reports where they disagree: an accelerator with no
    code, code with no accelerator, or a mismatch between them.
    """

    slug: str = Field(description="The accelerator the issue is about")
    issue_type: str = Field(
        description='One of "undocumented", "no_code" or "mismatch"'
    )
    message: str = Field(description="What is wrong, in a sentence")


class IntegrationReference(Entity):
    """Reference to an integration with optional description.

    Used for sources_from and publishes_to relationships where
    an accelerator may specify what data it sources or publishes.
    """

    slug: str = Field(description='Integration slug (e.g., "pilot-data-collection")')
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


class Accelerator(Entity):
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
    sources_from: tuple[IntegrationReference, ...] = Field(
        default_factory=tuple, description="Integrations this accelerator reads from"
    )
    feeds_into: tuple[str, ...] = Field(
        default_factory=tuple, description="Other accelerators this one feeds data into"
    )
    publishes_to: tuple[IntegrationReference, ...] = Field(
        default_factory=tuple, description="Integrations this accelerator writes to"
    )
    depends_on: tuple[str, ...] = Field(
        default_factory=tuple, description="Other accelerators this one depends on"
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
