"""Contrib module domain model.

Represents a reusable contrib module in the HCD documentation system.
Contrib modules are utilities that solutions can use, distinct from
accelerators (bounded contexts for conceptualizing solutions).
"""

from pydantic import BaseModel, field_validator


class ContribModule(BaseModel):
    """Contrib module entity.

    A contrib module represents a reusable utility that solutions can use.
    Unlike accelerators (bounded contexts for patterns), contrib modules
    are runtime utilities like polling workflows, authentication helpers, etc.
    """

    slug: str
    name: str = ""
    description: str = ""
    technology: str = "Python"
    docname: str = ""
    code_path: str = ""
    solution_slug: str = ""

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
        if self.name:
            return self.name
        return self.slug.replace("-", " ").title()

    @property
    def c4_description(self) -> str:
        """Get description for C4 container diagrams."""
        if self.description:
            return self.description
        return f"{self.display_title} utility"
