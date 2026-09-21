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
