"""Shared domain services.

Service protocols for the core/shared bounded context.
"""

from .handler import Handler
from .semantic_relation_registry import (
    RELATION_LABELS,
    RelationEdge,
    SemanticRelationRegistry,
    get_forward_label,
    get_inverse_label,
    get_relation_slug_attr,
)

__all__ = [
    # Handler pattern
    "Handler",
    # Semantic relation registry
    "RelationEdge",
    "SemanticRelationRegistry",
    "RELATION_LABELS",
    "get_forward_label",
    "get_inverse_label",
    "get_relation_slug_attr",
]
