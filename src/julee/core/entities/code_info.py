"""Code introspection domain models.

Models for representing Python code structure extracted via AST parsing.
These are core concepts of Clean Architecture - viewpoint accelerators
(HCD, C4) project onto these foundational models.

Used for:
- CLI introspection (julee-admin)
- Documentation generation
- Architecture validation
"""

from pydantic import BaseModel, Field, field_validator


class FieldInfo(BaseModel):
    """Information about a class field/attribute."""

    name: str
    type_annotation: str = ""
    default: str | None = None


class ParameterInfo(BaseModel):
    """Information about a method parameter."""

    name: str
    type_annotation: str = ""


class MethodInfo(BaseModel):
    """Information about a class method."""

    name: str
    is_async: bool = False
    parameters: list[ParameterInfo] = Field(default_factory=list)
    return_type: str = ""
    docstring: str = ""
    source: str = ""

    @property
    def parameter_names(self) -> list[str]:
        """Get list of parameter names (for backward compatibility)."""
        return [p.name for p in self.parameters]

    @property
    def parameter_types(self) -> list[str]:
        """Get list of parameter type annotations."""
        return [p.type_annotation for p in self.parameters]

    @property
    def referenced_types(self) -> set[str]:
        """Get all type names referenced in this method's signature.

        Extracts type names from parameter types and return type.
        Handles generics like list[Foo] by extracting Foo.
        """
        import re

        types: set[str] = set()
        all_annotations = self.parameter_types + [self.return_type]

        for annotation in all_annotations:
            if not annotation:
                continue
            # Extract all capitalized identifiers (likely type names)
            # This handles: Foo, list[Foo], dict[str, Foo], Foo | Bar
            matches = re.findall(r"\b([A-Z][a-zA-Z0-9]*)\b", annotation)
            types.update(matches)

        return types


class ClassInfo(BaseModel):
    """Information about a Python class extracted via AST.

    Represents any discoverable class in a bounded context's domain layer:
    entities, use cases, repository protocols, service protocols.
    """

    name: str
    docstring: str = ""
    file: str = ""
    bases: list[str] = Field(default_factory=list)
    fields: list[FieldInfo] = Field(default_factory=list)
    methods: list[MethodInfo] = Field(default_factory=list)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @property
    def referenced_types(self) -> set[str]:
        """Get all type names referenced in this class's method signatures.

        Aggregates referenced types from all methods. Used for determining
        which entity types a service protocol is bound to.
        """
        types: set[str] = set()
        for method in self.methods:
            types.update(method.referenced_types)
        return types


from julee.core.entities.pipeline import Pipeline  # noqa: E402


class BoundedContextInfo(BaseModel):
    """Information about a bounded context's code structure.

    Represents the Clean Architecture layers present in a bounded context:
    - entities (domain/models/)
    - use_cases (domain/use_cases/)
    - repository_protocols (domain/repositories/)
    - service_protocols (domain/services/)

    This is a foundational model that viewpoint accelerators project onto.
    For example, HCD's Accelerator model is ontologically bound to this.
    """

    slug: str
    entities: list[ClassInfo] = Field(default_factory=list)
    use_cases: list[ClassInfo] = Field(default_factory=list)
    requests: list[ClassInfo] = Field(default_factory=list)
    responses: list[ClassInfo] = Field(default_factory=list)
    repository_protocols: list[ClassInfo] = Field(default_factory=list)
    service_protocols: list[ClassInfo] = Field(default_factory=list)
    pipelines: list[Pipeline] = Field(default_factory=list)
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
    def pipeline_count(self) -> int:
        """Get number of pipelines."""
        return len(self.pipelines)

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
        if self.pipelines:
            parts.append(f"{len(self.pipelines)} pipelines")
        return ", ".join(parts) if parts else "empty"
