"""BoundedContext domain model.

Represents a bounded context (accelerator) as a code structure, independent
of any viewpoint projection. This is the foundational entity that viewpoints
like HCD and C4 are ontologically bound to.

The term "bounded context" comes from Domain-Driven Design and represents
a clear boundary around a domain model where specific terms have specific
meanings. In julee, bounded contexts follow Clean Architecture patterns
and "scream" at the top level of the codebase.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class StructuralMarkers:
    """Structural markers indicating what a bounded context contains.

    These markers reflect the Clean Architecture layers present in a
    bounded context. Supports both flattened structure ({bc}/entities/)
    and legacy structure ({bc}/domain/models/).
    """

    # Core Clean Architecture layers
    has_domain_models: bool = False
    has_domain_repositories: bool = False
    has_domain_services: bool = False
    has_domain_use_cases: bool = False

    # Additional structural elements
    has_tests: bool = False
    has_parsers: bool = False
    has_serializers: bool = False

    @property
    def has_clean_architecture_layers(self) -> bool:
        """True if context has recognizable CA layer structure."""
        return self.has_domain_models or self.has_domain_use_cases


@dataclass(frozen=True)
class BoundedContext:
    """A linguistic and conceptual boundary around a domain model.

    In Domain-Driven Design, a bounded context defines the scope within which
    a particular domain model applies. The same word can mean different things
    in different contexts - "Account" means something different in Banking vs
    Authentication. The bounded context makes these distinctions explicit.

    In Clean Architecture terms, each bounded context is an independent
    deployable unit with its own domain layer, use cases, and infrastructure.
    Dependencies between contexts flow through well-defined interfaces, never
    through shared domain models.

    Julee's "Screaming Architecture" places bounded contexts at the top level
    of the codebase. When you open the src/ directory, the first thing you see
    are the business capabilities: hcd/, c4/, ceap/, polling/. The architecture
    screams what the system does, not what frameworks it uses.
    """

    # Identity
    slug: str
    """Directory name / import path segment."""

    path: str
    """Filesystem path relative to project root."""

    description: str | None = None
    """First line of __init__.py docstring, if present."""

    # Classification
    is_nested: bool = False
    """True if discovered inside a nested solution rather than at the top
    level of the search root."""

    is_viewpoint: bool = False
    """True if this context describes a solution rather than implementing
    a domain. Declared by the kit that provides it."""

    # Structure
    markers: StructuralMarkers = field(default_factory=StructuralMarkers)
    """What structural elements this context contains."""

    def __post_init__(self) -> None:
        """Check the slug is not empty, and trim it.

        This was a ``field_validator`` in ``mode="before"``. It both
        refused an empty slug and returned a stripped one, so it decided
        what the field holds rather than only checking it, and the
        stripping has to survive the conversion or a context read from a
        padded directory name stops matching its own import path.

        Raises:
            ValueError: If the slug is empty or only whitespace
        """
        if not self.slug or not self.slug.strip():
            raise ValueError("slug cannot be empty")
        object.__setattr__(self, "slug", self.slug.strip())

    @property
    def absolute_path(self) -> Path:
        """Get path as a Path object."""
        return Path(self.path)

    @property
    def import_path(self) -> str:
        """Get the Python import path for this context.

        Example: "julee.contrib.ceap" or "julee_polling"
        """
        parts = Path(self.path).parts
        # Find the last 'src' and take everything after it
        for i in range(len(parts) - 1, -1, -1):
            if parts[i] == "src":
                return ".".join(parts[i + 1 :])
        # No 'src' in path, filter out root and empty parts
        return ".".join(p for p in parts if p and p != "/")

    @property
    def display_name(self) -> str:
        """Human-readable name derived from slug."""
        return self.slug.replace("-", " ").replace("_", " ").title()

    def has_layer(self, layer: str) -> bool:
        """Check if context has a specific CA layer.

        Args:
            layer: One of "models", "repositories", "services", "use_cases"

        Returns:
            True if the layer exists
        """
        if layer == "models":
            return self.markers.has_domain_models
        if layer == "repositories":
            return self.markers.has_domain_repositories
        if layer == "services":
            return self.markers.has_domain_services
        if layer == "use_cases":
            return self.markers.has_domain_use_cases
        return False
