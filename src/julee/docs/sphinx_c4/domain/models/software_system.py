"""SoftwareSystem domain model.

The highest level of abstraction in C4 - something that delivers value to users.
"""

from enum import Enum

from pydantic import BaseModel, Field, computed_field, field_validator

from ...utils import normalize_name, slugify


class SystemType(str, Enum):
    """Classification of software systems."""

    INTERNAL = "internal"  # Owned/developed by the organization
    EXTERNAL = "external"  # Third-party systems
    EXISTING = "existing"  # Legacy systems being integrated


class SoftwareSystem(BaseModel):
    """Software System entity.

    The highest level of abstraction in C4. Represents something that
    delivers value to its users, whether human or not.

    Attributes:
        slug: URL-safe identifier (e.g., "banking-system")
        name: Display name (e.g., "Internet Banking System")
        description: Brief description of what the system does
        system_type: Classification (internal, external, existing)
        owner: Team or organization that owns this system
        technology: High-level technology stack description
        url: Link to system documentation or interface
        tags: Arbitrary tags for filtering/grouping
        docname: RST document where defined (for Sphinx incremental builds)
    """

    slug: str
    name: str
    description: str = ""
    system_type: SystemType = SystemType.INTERNAL
    owner: str = ""
    technology: str = ""
    url: str = ""
    tags: list[str] = Field(default_factory=list)
    docname: str = ""

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate and normalize slug."""
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return slugify(v.strip())

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @computed_field
    @property
    def name_normalized(self) -> str:
        """Normalized name for case-insensitive matching."""
        return normalize_name(self.name)

    @property
    def display_title(self) -> str:
        """Formatted title for display."""
        return self.name

    @property
    def is_external(self) -> bool:
        """Check if this is an external system."""
        return self.system_type == SystemType.EXTERNAL

    @property
    def is_internal(self) -> bool:
        """Check if this is an internal system."""
        return self.system_type == SystemType.INTERNAL

    def has_tag(self, tag: str) -> bool:
        """Check if system has a specific tag (case-insensitive)."""
        return tag.lower() in [t.lower() for t in self.tags]

    def add_tag(self, tag: str) -> None:
        """Add a tag if not already present."""
        if not self.has_tag(tag):
            self.tags.append(tag)
