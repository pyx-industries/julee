"""Code introspection domain models.

Models for representing Python code structure extracted via AST parsing.
Used to document bounded contexts and their ADR 001-compliant structure.
"""

from pydantic import BaseModel, Field, field_validator


class ClassInfo(BaseModel):
    """Information about a Python class extracted via AST."""

    name: str
    docstring: str = ""
    file: str = ""

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()


class BoundedContextInfo(BaseModel):
    """Information about a bounded context's code structure.

    Represents the ADR 001-compliant structure of a bounded context
    with domain models, use cases, and repository/service protocols.
    """

    slug: str
    entities: list[ClassInfo] = Field(default_factory=list)
    use_cases: list[ClassInfo] = Field(default_factory=list)
    repository_protocols: list[ClassInfo] = Field(default_factory=list)
    service_protocols: list[ClassInfo] = Field(default_factory=list)
    has_infrastructure: bool = False
    code_dir: str = ""
    objective: str | None = None
    docstring: str | None = None

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug is not empty."""
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @property
    def entity_count(self) -> int:
        """Get number of domain entities."""
        return len(self.entities)

    @property
    def use_case_count(self) -> int:
        """Get number of use cases."""
        return len(self.use_cases)

    @property
    def protocol_count(self) -> int:
        """Get total number of protocols (repository + service)."""
        return len(self.repository_protocols) + len(self.service_protocols)

    @property
    def has_entities(self) -> bool:
        """Check if bounded context has any entities."""
        return len(self.entities) > 0

    @property
    def has_use_cases(self) -> bool:
        """Check if bounded context has any use cases."""
        return len(self.use_cases) > 0

    @property
    def has_protocols(self) -> bool:
        """Check if bounded context has any protocols."""
        return self.protocol_count > 0

    def get_entity_names(self) -> list[str]:
        """Get list of entity class names."""
        return [e.name for e in self.entities]

    def get_use_case_names(self) -> list[str]:
        """Get list of use case class names."""
        return [u.name for u in self.use_cases]

    def summary(self) -> str:
        """Get a brief summary of the bounded context.

        Returns:
            Summary string like "3 entities, 2 use cases"
        """
        parts = []
        if self.entities:
            parts.append(f"{len(self.entities)} entities")
        if self.use_cases:
            parts.append(f"{len(self.use_cases)} use cases")
        if self.repository_protocols:
            parts.append(f"{len(self.repository_protocols)} repository protocols")
        if self.service_protocols:
            parts.append(f"{len(self.service_protocols)} service protocols")
        return ", ".join(parts) if parts else "empty"
