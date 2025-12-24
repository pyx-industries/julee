"""Component domain model.

A grouping of related functionality within a container.
"""

from pydantic import BaseModel, Field, computed_field, field_validator

from julee.c4.utils import normalize_name, slugify


class Component(BaseModel):
    """Component entity.

    A component is a grouping of related functionality encapsulated
    behind a well-defined interface. Components exist within containers
    and are NOT separately deployable units.
    """

    slug: str
    name: str
    container_slug: str
    system_slug: str
    description: str = ""
    technology: str = ""
    interface: str = ""
    code_path: str = ""
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

    @field_validator("container_slug", mode="before")
    @classmethod
    def validate_container_slug(cls, v: str) -> str:
        """Validate container_slug is not empty."""
        if not v or not v.strip():
            raise ValueError("container_slug cannot be empty")
        return v.strip()

    @field_validator("system_slug", mode="before")
    @classmethod
    def validate_system_slug(cls, v: str) -> str:
        """Validate system_slug is not empty."""
        if not v or not v.strip():
            raise ValueError("system_slug cannot be empty")
        return v.strip()

    @computed_field
    @property
    def name_normalized(self) -> str:
        """Normalized name for case-insensitive matching."""
        return normalize_name(self.name)

    @property
    def qualified_slug(self) -> str:
        """Fully qualified slug including container and system."""
        return f"{self.system_slug}/{self.container_slug}/{self.slug}"

    @property
    def has_code(self) -> bool:
        """Check if component has linked code."""
        return bool(self.code_path)

    @property
    def has_interface(self) -> bool:
        """Check if component has interface description."""
        return bool(self.interface)

    def has_tag(self, tag: str) -> bool:
        """Check if component has a specific tag (case-insensitive)."""
        return tag.lower() in [t.lower() for t in self.tags]

    def add_tag(self, tag: str) -> None:
        """Add a tag if not already present."""
        if not self.has_tag(tag):
            self.tags.append(tag)
