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
    decorators: list[str] = Field(default_factory=list)
    """Dotted paths of the class's decorators, imports followed.

    ``@temporal_activity_registration("x")`` and an aliased
    ``@t.temporal_activity_registration`` both record
    ``julee.integrations.temporal.decorators.temporal_activity_registration``
    as far as the import can be followed, so a rule matches on the path
    rather than on how the decorator was spelled at the point of use.
    """
    decorator_arguments: dict[str, dict[str, str]] = Field(default_factory=dict)
    """Keyword arguments each decorator was called with, as source text.

    Keyed by the decorator's last path segment, matching how
    ``decorated_with`` reads: ``{"dataclass": {"frozen": "True"}}``. A
    decorator applied bare has no entry.

    Source text, not values, because a class is read rather than
    imported. ``frozen=True`` is the string ``"True"``, and
    ``frozen=SOME_CONSTANT`` is ``"SOME_CONSTANT"`` — which a rule
    should read as not knowing, rather than guess at.
    """

    def decorated_with(self, name: str) -> bool:
        """Whether a decorator of this name is applied to the class.

        Matches on the last segment of the dotted path, because a
        decorator re-exported from a package and imported from the module
        that defines it resolve to two different paths and are the same
        decorator.

        Args:
            name: Decorator name, e.g. "temporal_activity_registration"

        Returns:
            True if any decorator ends in that name
        """
        return any(path.rsplit(".", 1)[-1] == name for path in self.decorators)

    def decorator_argument(self, name: str, keyword: str) -> str | None:
        """What a decorator was passed for one keyword, as written.

        The source text rather than a value, because this is read from a
        file and not executed: ``@dataclass(frozen=True)`` gives
        ``"True"``, and ``@dataclass(frozen=FROZEN)`` gives ``"FROZEN"``,
        which a caller should treat as not knowing rather than as true.

        Args:
            name: Decorator name, matched as ``decorated_with`` does
            keyword: The keyword argument to look for

        Returns:
            The argument's source, or None if the decorator is absent,
            was applied bare, or was not given that keyword
        """
        return self.decorator_arguments.get(name, {}).get(keyword)

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
