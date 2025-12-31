"""Semantic relation registry for entity type relationship traversal.

The SemanticRelationRegistry provides domain logic for understanding how
entity types relate across bounded contexts. It maintains an index of
semantic relations declared via the @semantic_relation decorator, enabling
both forward and reverse lookups.

Why This Exists
---------------

Entities declare semantic relations to express architectural intent:

    @semantic_relation(BoundedContext, RelationType.PROJECTS)
    class Accelerator(BaseModel):
        '''Accelerator projects a view onto BoundedContext.'''

    @semantic_relation(UseCase, RelationType.ENABLES)
    @semantic_relation(Persona, RelationType.REFERENCES)
    class Story(BaseModel):
        '''Story is enabled by UseCases and references Personas.'''

These declarations create a graph of relationships between entity types.
The registry indexes this graph for efficient traversal in both directions:

- Forward: "What does Accelerator relate to?" -> [BoundedContext via PROJECTS]
- Reverse: "What relates to BoundedContext?" -> [Accelerator via PROJECTS]

This enables documentation infrastructure to generate bidirectional
cross-references without hardcoding entity-to-entity mappings.


Relation Vocabulary
-------------------

Each relation type has forward and inverse labels for documentation:

    PROJECTS:   "Projects" / "Projected by"
    ENABLES:    "Enables" / "Enabled by"
    REFERENCES: "References" / "Referenced by"
    PART_OF:    "Part of" / "Contains"

The vocabulary is a domain concept - it defines how we talk about
relationships in documentation, not how we render them.


Usage
-----

Register entity types at application startup:

    registry = SemanticRelationRegistry()
    registry.register(Accelerator)
    registry.register(Story)
    registry.register(Epic)

Query relations:

    # Forward: what does Story relate to?
    outbound = registry.get_outbound_relations(Story)
    # [RelationEdge(ENABLES, Story, UseCase),
    #  RelationEdge(REFERENCES, Story, Persona)]

    # Reverse: what relates to UseCase?
    inbound = registry.get_inbound_relations(UseCase)
    # [RelationEdge(ENABLES, Story, UseCase)]

Infrastructure (Sphinx, etc.) uses these queries to generate links.


Design Notes
------------

This is a domain service, not infrastructure. It understands the domain
concept of semantic relations but knows nothing about:

- Documentation URLs
- HTML rendering
- Sphinx directives
- File systems

Those concerns belong in infrastructure adapters that consume this service.
"""

from __future__ import annotations

import importlib
import inspect
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel

from julee.core.decorators import get_semantic_relations
from julee.core.entities.semantic_relation import RelationType

if TYPE_CHECKING:
    from types import ModuleType


# =============================================================================
# Relation Vocabulary
# =============================================================================

RELATION_LABELS: dict[RelationType, tuple[str, str]] = {
    # (forward_label, inverse_label)
    RelationType.PROJECTS: ("Projects", "Projected by"),
    RelationType.ENABLES: ("Enables", "Enabled by"),
    RelationType.REFERENCES: ("References", "Referenced by"),
    RelationType.PART_OF: ("Part of", "Contains"),
    RelationType.CONTAINS: ("Contains", "Part of"),
    RelationType.IS_A: ("Is a", "Specializations"),
    RelationType.IMPLEMENTS: ("Implements", "Implemented by"),
    RelationType.BROADER: ("Broader", "Narrower"),
    RelationType.NARROWER: ("Narrower", "Broader"),
    RelationType.RELATED: ("Related to", "Related to"),
}


def get_forward_label(relation_type: RelationType) -> str:
    """Get the forward direction label for a relation type.

    Args:
        relation_type: The relation type

    Returns:
        Human-readable label for forward direction (e.g., "Projects")
    """
    return RELATION_LABELS.get(relation_type, ("Related to", "Related to"))[0]


def get_inverse_label(relation_type: RelationType) -> str:
    """Get the inverse direction label for a relation type.

    Args:
        relation_type: The relation type

    Returns:
        Human-readable label for inverse direction (e.g., "Projected by")
    """
    return RELATION_LABELS.get(relation_type, ("Related to", "Related to"))[1]


# =============================================================================
# Data Structures
# =============================================================================


@dataclass(frozen=True)
class RelationEdge:
    """An edge in the semantic relation graph.

    Represents a directed relationship from source_type to target_type.
    """

    relation_type: RelationType
    source_type: type
    target_type: type

    @property
    def forward_label(self) -> str:
        """Label for source -> target direction."""
        return get_forward_label(self.relation_type)

    @property
    def inverse_label(self) -> str:
        """Label for target -> source direction."""
        return get_inverse_label(self.relation_type)

    def __repr__(self) -> str:
        return (
            f"RelationEdge({self.source_type.__name__} "
            f"-[{self.relation_type.value}]-> "
            f"{self.target_type.__name__})"
        )


# =============================================================================
# Registry
# =============================================================================


class SemanticRelationRegistry:
    """Registry of entity types for semantic relation traversal.

    Maintains an index enabling both forward and reverse relation lookups
    across entity types. Types must be explicitly registered.

    Thread Safety:
        This implementation is not thread-safe. For concurrent access,
        use appropriate synchronization or create separate instances.
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._types: set[type] = set()
        self._outbound_index: dict[type, list[RelationEdge]] = {}
        self._inbound_index: dict[type, list[RelationEdge]] = {}

    def register(self, entity_type: type) -> None:
        """Register an entity type and index its semantic relations.

        Reads the __semantic_relations__ attribute populated by the
        @semantic_relation decorator and indexes for bidirectional lookup.

        Args:
            entity_type: Entity class to register

        Note:
            Re-registering the same type is a no-op.
        """
        if entity_type in self._types:
            return

        self._types.add(entity_type)

        # Index all declared relations
        for rel in get_semantic_relations(entity_type):
            edge = RelationEdge(
                relation_type=rel.relation_type,
                source_type=entity_type,
                target_type=rel.target_type,
            )

            # Outbound index: source -> [edges]
            if entity_type not in self._outbound_index:
                self._outbound_index[entity_type] = []
            self._outbound_index[entity_type].append(edge)

            # Inbound index: target -> [edges]
            target = rel.target_type
            if target not in self._inbound_index:
                self._inbound_index[target] = []
            self._inbound_index[target].append(edge)

    def register_all(self, entity_types: list[type]) -> None:
        """Register multiple entity types.

        Args:
            entity_types: List of entity classes to register
        """
        for entity_type in entity_types:
            self.register(entity_type)

    def register_from_module(self, module: "ModuleType | str") -> int:
        """Register all entity types from a module.

        Scans the module for BaseModel subclasses with __semantic_relations__
        and registers them.

        Args:
            module: Module object or dotted module path string

        Returns:
            Number of types registered
        """
        if isinstance(module, str):
            module = importlib.import_module(module)

        count = 0
        for _name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, BaseModel)
                and obj is not BaseModel
                and hasattr(obj, "__semantic_relations__")
                and obj.__semantic_relations__  # Non-empty
            ):
                self.register(obj)
                count += 1

        return count

    def get_outbound_relations(self, entity_type: type) -> list[RelationEdge]:
        """Get all outbound relations declared by an entity type.

        Returns edges where entity_type is the source.

        Args:
            entity_type: The source entity type

        Returns:
            List of RelationEdge objects (source -> target)
        """
        return self._outbound_index.get(entity_type, []).copy()

    def get_inbound_relations(self, entity_type: type) -> list[RelationEdge]:
        """Get all inbound relations pointing to an entity type.

        Returns edges where entity_type is the target. Requires that
        the source types have been registered.

        Args:
            entity_type: The target entity type

        Returns:
            List of RelationEdge objects (source -> target)
        """
        return self._inbound_index.get(entity_type, []).copy()

    def get_relations_by_type(
        self,
        entity_type: type,
        relation_type: RelationType,
        *,
        direction: str = "outbound",
    ) -> list[RelationEdge]:
        """Get relations of a specific type for an entity.

        Args:
            entity_type: The entity type to query
            relation_type: Filter to this relation type
            direction: "outbound" or "inbound"

        Returns:
            Filtered list of RelationEdge objects
        """
        if direction == "outbound":
            edges = self.get_outbound_relations(entity_type)
        elif direction == "inbound":
            edges = self.get_inbound_relations(entity_type)
        else:
            raise ValueError(f"direction must be 'outbound' or 'inbound', got {direction!r}")

        return [e for e in edges if e.relation_type == relation_type]

    def get_projection_target(self, entity_type: type) -> type | None:
        """Get the type this entity projects onto, if any.

        Convenience method for the common case of finding what a
        viewpoint entity projects onto (via PROJECTS relation).

        Args:
            entity_type: The entity type to query

        Returns:
            Target type of PROJECTS relation, or None
        """
        edges = self.get_relations_by_type(
            entity_type, RelationType.PROJECTS, direction="outbound"
        )
        return edges[0].target_type if edges else None

    @property
    def registered_types(self) -> frozenset[type]:
        """All registered entity types."""
        return frozenset(self._types)

    def __len__(self) -> int:
        """Number of registered types."""
        return len(self._types)

    def __contains__(self, entity_type: type) -> bool:
        """Check if a type is registered."""
        return entity_type in self._types


# =============================================================================
# Slug Attribute Convention
# =============================================================================


def get_relation_slug_attr(target_type: type) -> str:
    """Get the conventional slug attribute name for a relation target.

    Convention: For a relation to TargetType, the source entity should
    have an attribute named `target_type_slug` (snake_case with _slug suffix).

    Examples:
        BoundedContext -> bounded_context_slug
        App -> app_slug
        Persona -> persona_slug

    Args:
        target_type: The target entity type

    Returns:
        Conventional attribute name for the target's slug
    """
    name = target_type.__name__
    # Convert CamelCase to snake_case
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    return f"{snake}_slug"


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "RelationEdge",
    "SemanticRelationRegistry",
    "RELATION_LABELS",
    "get_forward_label",
    "get_inverse_label",
    "get_relation_slug_attr",
]
