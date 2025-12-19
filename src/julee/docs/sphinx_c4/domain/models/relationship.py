"""Relationship domain model.

Connections between C4 elements representing interactions.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator

from ...utils import slugify


class ElementType(str, Enum):
    """Types of elements that can participate in relationships."""

    PERSON = "person"  # References HCD Persona by normalized_name
    SOFTWARE_SYSTEM = "software_system"
    CONTAINER = "container"
    COMPONENT = "component"


class Relationship(BaseModel):
    """Relationship entity.

    Represents a connection between two C4 elements. Relationships have
    a source, destination, and description of the interaction.

    When source_type or destination_type is PERSON, the corresponding slug
    should be the persona's normalized_name, which references an HCD Persona.

    Attributes:
        slug: URL-safe identifier (auto-generated from source/destination if empty)
        source_type: Type of source element
        source_slug: Slug of source element (or persona normalized_name)
        destination_type: Type of destination element
        destination_slug: Slug of destination element (or persona normalized_name)
        description: What this relationship represents (e.g., "Reads from")
        technology: Protocol/technology used (e.g., "HTTPS/JSON")
        tags: Arbitrary tags for filtering
        bidirectional: Whether relationship goes both ways
        docname: RST document where defined
    """

    slug: str = ""
    source_type: ElementType
    source_slug: str
    destination_type: ElementType
    destination_slug: str
    description: str = "Uses"
    technology: str = ""
    tags: list[str] = Field(default_factory=list)
    bidirectional: bool = False
    docname: str = ""

    def model_post_init(self, __context) -> None:
        """Generate slug if not provided."""
        if not self.slug:
            object.__setattr__(self, "slug", self._generate_slug())

    def _generate_slug(self) -> str:
        """Generate a deterministic slug from source and destination."""
        return slugify(f"{self.source_slug}-to-{self.destination_slug}")

    @field_validator("source_slug", mode="before")
    @classmethod
    def validate_source_slug(cls, v: str) -> str:
        """Validate source_slug is not empty."""
        if not v or not v.strip():
            raise ValueError("source_slug cannot be empty")
        return v.strip()

    @field_validator("destination_slug", mode="before")
    @classmethod
    def validate_destination_slug(cls, v: str) -> str:
        """Validate destination_slug is not empty."""
        if not v or not v.strip():
            raise ValueError("destination_slug cannot be empty")
        return v.strip()

    @property
    def is_person_relationship(self) -> bool:
        """Check if this relationship involves a person."""
        return (
            self.source_type == ElementType.PERSON
            or self.destination_type == ElementType.PERSON
        )

    @property
    def is_cross_system(self) -> bool:
        """Check if relationship crosses system boundaries."""
        return (
            self.source_type == ElementType.SOFTWARE_SYSTEM
            or self.destination_type == ElementType.SOFTWARE_SYSTEM
        )

    @property
    def is_internal(self) -> bool:
        """Check if relationship is between containers/components only."""
        internal_types = {ElementType.CONTAINER, ElementType.COMPONENT}
        return (
            self.source_type in internal_types
            and self.destination_type in internal_types
        )

    @property
    def label(self) -> str:
        """Get formatted label for diagram rendering."""
        if self.technology:
            return f"{self.description}\\n[{self.technology}]"
        return self.description

    def involves_element(self, element_type: ElementType, element_slug: str) -> bool:
        """Check if relationship involves a specific element."""
        return (
            self.source_type == element_type
            and self.source_slug == element_slug
        ) or (
            self.destination_type == element_type
            and self.destination_slug == element_slug
        )

    def involves_system(self, system_slug: str) -> bool:
        """Check if relationship involves a specific system."""
        return self.involves_element(ElementType.SOFTWARE_SYSTEM, system_slug)

    def involves_container(self, container_slug: str) -> bool:
        """Check if relationship involves a specific container."""
        return self.involves_element(ElementType.CONTAINER, container_slug)

    def involves_component(self, component_slug: str) -> bool:
        """Check if relationship involves a specific component."""
        return self.involves_element(ElementType.COMPONENT, component_slug)

    def involves_person(self, persona_name: str) -> bool:
        """Check if relationship involves a specific persona."""
        return self.involves_element(ElementType.PERSON, persona_name)

    def has_tag(self, tag: str) -> bool:
        """Check if relationship has a specific tag (case-insensitive)."""
        return tag.lower() in [t.lower() for t in self.tags]
