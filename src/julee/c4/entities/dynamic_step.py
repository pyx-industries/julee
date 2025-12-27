"""DynamicStep domain model.

A numbered step in a dynamic (sequence) diagram.
"""

from pydantic import BaseModel, field_validator

from julee.c4.utils import slugify

from .relationship import ElementType


class DynamicStep(BaseModel):
    """DynamicStep entity.

    Represents a numbered interaction in a dynamic diagram.
    Dynamic diagrams show runtime behavior for specific scenarios
    (user stories, use cases, features).
    """

    slug: str
    sequence_name: str
    step_number: int
    source_type: ElementType
    source_slug: str
    destination_type: ElementType
    destination_slug: str
    description: str = ""
    technology: str = ""
    return_value: str = ""
    is_async: bool = False
    docname: str = ""

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate and normalize slug."""
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @field_validator("sequence_name", mode="before")
    @classmethod
    def validate_sequence_name(cls, v: str) -> str:
        """Validate sequence_name is not empty."""
        if not v or not v.strip():
            raise ValueError("sequence_name cannot be empty")
        return v.strip()

    @field_validator("step_number")
    @classmethod
    def validate_step_number(cls, v: int) -> int:
        """Validate step_number is positive."""
        if v < 1:
            raise ValueError("step_number must be >= 1")
        return v

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
    def step_label(self) -> str:
        """Get formatted step label (e.g., '1. ')."""
        return f"{self.step_number}. "

    @property
    def full_label(self) -> str:
        """Get full step label with description."""
        base = f"{self.step_number}. {self.description}"
        if self.technology:
            base = f"{base} [{self.technology}]"
        return base

    @property
    def is_person_interaction(self) -> bool:
        """Check if this step involves a person."""
        return (
            self.source_type == ElementType.PERSON
            or self.destination_type == ElementType.PERSON
        )

    @classmethod
    def generate_slug(cls, sequence_name: str, step_number: int) -> str:
        """Generate slug from sequence and step number."""
        return f"{slugify(sequence_name)}-step-{step_number}"

    @classmethod
    def from_create_data(
        cls,
        sequence_name: str,
        step_number: int,
        source_type: ElementType,
        source_slug: str,
        destination_type: ElementType,
        destination_slug: str,
        slug: str = "",
        description: str = "",
        technology: str = "",
        return_value: str = "",
        is_async: bool = False,
        docname: str = "",
    ) -> "DynamicStep":
        """Create entity from request data, auto-generating slug if empty.

        Used by generic CRUD CreateUseCase to support auto-slug generation.
        The slug parameter is optional - if empty, it's generated from
        sequence_name and step_number.
        """
        if not slug:
            slug = cls.generate_slug(sequence_name, step_number)
        return cls(
            slug=slug,
            sequence_name=sequence_name,
            step_number=step_number,
            source_type=source_type,
            source_slug=source_slug,
            destination_type=destination_type,
            destination_slug=destination_slug,
            description=description,
            technology=technology,
            return_value=return_value,
            is_async=is_async,
            docname=docname,
        )

    def involves_element(self, element_type: ElementType, element_slug: str) -> bool:
        """Check if step involves a specific element."""
        return (
            self.source_type == element_type and self.source_slug == element_slug
        ) or (
            self.destination_type == element_type
            and self.destination_slug == element_slug
        )
