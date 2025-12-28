"""Accelerator domain model.

An accelerator is a collection of pipelines that work together to make an area
of business go faster.

Julee is a framework for accountable and transparent digital supply chains.
Accelerators are how solutions deliver that value - automating business processes
that would otherwise be slow and manual, while maintaining the audit trails
needed for compliance and due diligence.

Structure
---------
A solution screams its accelerators::

    solution/
      src/
        accelerator_a/
          entities/
          use_cases/
          infrastructure/
        accelerator_b/
          entities/
          use_cases/
          infrastructure/
      apps/
        api/
        cli/
        worker/

Each accelerator is a top-level package in ``src/``. The solution's architecture
speaks its business language.

Accelerators are bounded contexts that provide business capabilities. They may
have associated code in ``src/{slug}/`` and are exposed through one or more
applications.
"""

from pydantic import BaseModel, Field, field_validator


class AcceleratorValidationIssue(BaseModel):
    """A validation issue found for an accelerator.

    Value object representing a single issue discovered during
    accelerator validation (comparing documentation to code structure).
    """

    slug: str
    issue_type: str  # "undocumented", "no_code", "mismatch"
    message: str


class IntegrationReference(BaseModel):
    """Reference to an integration with optional description.

    Used for sources_from and publishes_to relationships where
    an accelerator may specify what data it sources or publishes.
    """

    slug: str
    description: str = ""

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

    slug: str
    name: str = ""
    status: str = ""
    milestone: str | None = None
    acceptance: str | None = None
    objective: str = ""
    sources_from: list[IntegrationReference] = Field(default_factory=list)
    feeds_into: list[str] = Field(default_factory=list)
    publishes_to: list[IntegrationReference] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    docname: str = ""

    # C4 mapping fields
    domain_concepts: list[str] = Field(default_factory=list)
    bounded_context_path: str = ""
    technology: str = "Python"

    # Document structure (RST round-trip)
    page_title: str = ""
    preamble_rst: str = ""
    epilogue_rst: str = ""

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug is not empty."""
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @classmethod
    def from_create_data(cls, **data) -> "Accelerator":
        """Create from CRUD request data (doctrine pattern for generic CRUD).

        Handles:
        - sources_from: list[dict] -> list[IntegrationReference]
        - publishes_to: list[dict] -> list[IntegrationReference]
        """
        # Convert sources_from dicts to IntegrationReference objects
        sources_from_raw = data.get("sources_from", [])
        data["sources_from"] = [
            IntegrationReference.from_dict(ref) if isinstance(ref, dict) else ref
            for ref in sources_from_raw
        ]

        # Convert publishes_to dicts to IntegrationReference objects
        publishes_to_raw = data.get("publishes_to", [])
        data["publishes_to"] = [
            IntegrationReference.from_dict(ref) if isinstance(ref, dict) else ref
            for ref in publishes_to_raw
        ]

        return cls(**data)

    def apply_update(self, **data) -> "Accelerator":
        """Apply update data, converting dicts to proper objects.

        Used by generic UpdateUseCase.
        """
        # Convert sources_from dicts to IntegrationReference objects
        if "sources_from" in data:
            data["sources_from"] = [
                IntegrationReference.from_dict(ref) if isinstance(ref, dict) else ref
                for ref in data["sources_from"]
            ]

        # Convert publishes_to dicts to IntegrationReference objects
        if "publishes_to" in data:
            data["publishes_to"] = [
                IntegrationReference.from_dict(ref) if isinstance(ref, dict) else ref
                for ref in data["publishes_to"]
            ]

        return self.model_copy(update=data)

    @property
    def display_title(self) -> str:
        """Get formatted title for display."""
        if self.name:
            return self.name
        return self.slug.replace("-", " ").title()

    @property
    def status_normalized(self) -> str:
        """Get normalized status for grouping."""
        return self.status.lower().strip() if self.status else ""

    @property
    def concepts_description(self) -> str:
        """Get comma-separated domain concepts for C4 diagrams."""
        if self.domain_concepts:
            return ", ".join(self.domain_concepts)
        return ""

    @property
    def c4_description(self) -> str:
        """Get description for C4 container diagrams."""
        if self.objective:
            return self.objective
        if self.domain_concepts:
            return self.concepts_description
        return f"{self.display_title} bounded context"

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
