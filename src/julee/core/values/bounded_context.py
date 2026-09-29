"""What a bounded context was found to contain.

Structural markers are facts about a directory, not something kept under
an id. They are a field of ``BoundedContext`` and were counted as a
second entity beside it (ADR 018).
"""

from dataclasses import dataclass


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
