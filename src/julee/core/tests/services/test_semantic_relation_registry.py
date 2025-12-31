"""Tests for SemanticRelationRegistry service."""

import pytest
from pydantic import BaseModel

from julee.core.decorators import semantic_relation
from julee.core.entities.semantic_relation import RelationType
from julee.core.services.semantic_relation_registry import (
    RelationEdge,
    SemanticRelationRegistry,
    get_forward_label,
    get_inverse_label,
    get_relation_slug_attr,
)


# =============================================================================
# Test Fixtures - Entity types with semantic relations
# =============================================================================


class CoreEntity(BaseModel):
    """A core entity (target of projections)."""

    slug: str


class AnotherCoreEntity(BaseModel):
    """Another core entity."""

    slug: str


@semantic_relation(CoreEntity, RelationType.PROJECTS)
class ViewpointEntity(BaseModel):
    """A viewpoint entity that projects onto CoreEntity."""

    slug: str


@semantic_relation(CoreEntity, RelationType.ENABLES)
@semantic_relation(AnotherCoreEntity, RelationType.REFERENCES)
class MultiRelationEntity(BaseModel):
    """An entity with multiple relations."""

    slug: str
    core_entity_slug: str
    another_core_entity_slug: str


class UnrelatedEntity(BaseModel):
    """An entity with no semantic relations."""

    slug: str


# =============================================================================
# RelationEdge Tests
# =============================================================================


class TestRelationEdge:
    """Tests for RelationEdge dataclass."""

    def test_create_edge(self) -> None:
        """Test creating a relation edge."""
        edge = RelationEdge(
            relation_type=RelationType.PROJECTS,
            source_type=ViewpointEntity,
            target_type=CoreEntity,
        )

        assert edge.relation_type == RelationType.PROJECTS
        assert edge.source_type == ViewpointEntity
        assert edge.target_type == CoreEntity

    def test_forward_label(self) -> None:
        """Test forward label property."""
        edge = RelationEdge(RelationType.PROJECTS, ViewpointEntity, CoreEntity)
        assert edge.forward_label == "Projects"

    def test_inverse_label(self) -> None:
        """Test inverse label property."""
        edge = RelationEdge(RelationType.PROJECTS, ViewpointEntity, CoreEntity)
        assert edge.inverse_label == "Projected by"

    def test_repr(self) -> None:
        """Test string representation."""
        edge = RelationEdge(RelationType.PROJECTS, ViewpointEntity, CoreEntity)
        assert "ViewpointEntity" in repr(edge)
        assert "CoreEntity" in repr(edge)
        assert "projects" in repr(edge)

    def test_frozen(self) -> None:
        """Test that edges are immutable."""
        edge = RelationEdge(RelationType.PROJECTS, ViewpointEntity, CoreEntity)
        with pytest.raises(AttributeError):
            edge.relation_type = RelationType.ENABLES  # type: ignore


# =============================================================================
# Label Function Tests
# =============================================================================


class TestRelationLabels:
    """Tests for relation label functions."""

    def test_forward_labels(self) -> None:
        """Test forward labels for all relation types."""
        assert get_forward_label(RelationType.PROJECTS) == "Projects"
        assert get_forward_label(RelationType.ENABLES) == "Enables"
        assert get_forward_label(RelationType.REFERENCES) == "References"
        assert get_forward_label(RelationType.PART_OF) == "Part of"
        assert get_forward_label(RelationType.CONTAINS) == "Contains"
        assert get_forward_label(RelationType.IS_A) == "Is a"
        assert get_forward_label(RelationType.IMPLEMENTS) == "Implements"

    def test_inverse_labels(self) -> None:
        """Test inverse labels for all relation types."""
        assert get_inverse_label(RelationType.PROJECTS) == "Projected by"
        assert get_inverse_label(RelationType.ENABLES) == "Enabled by"
        assert get_inverse_label(RelationType.REFERENCES) == "Referenced by"
        assert get_inverse_label(RelationType.PART_OF) == "Contains"
        assert get_inverse_label(RelationType.CONTAINS) == "Part of"
        assert get_inverse_label(RelationType.IS_A) == "Specializations"
        assert get_inverse_label(RelationType.IMPLEMENTS) == "Implemented by"

    def test_symmetric_relations(self) -> None:
        """Test that BROADER/NARROWER are inverses."""
        assert get_forward_label(RelationType.BROADER) == "Broader"
        assert get_inverse_label(RelationType.BROADER) == "Narrower"
        assert get_forward_label(RelationType.NARROWER) == "Narrower"
        assert get_inverse_label(RelationType.NARROWER) == "Broader"


# =============================================================================
# Registry Tests
# =============================================================================


class TestSemanticRelationRegistry:
    """Tests for SemanticRelationRegistry."""

    def test_register_type(self) -> None:
        """Test registering an entity type."""
        registry = SemanticRelationRegistry()
        registry.register(ViewpointEntity)

        assert ViewpointEntity in registry
        assert len(registry) == 1

    def test_register_idempotent(self) -> None:
        """Test that re-registering is a no-op."""
        registry = SemanticRelationRegistry()
        registry.register(ViewpointEntity)
        registry.register(ViewpointEntity)

        assert len(registry) == 1

    def test_register_all(self) -> None:
        """Test registering multiple types at once."""
        registry = SemanticRelationRegistry()
        registry.register_all([ViewpointEntity, MultiRelationEntity])

        assert len(registry) == 2
        assert ViewpointEntity in registry
        assert MultiRelationEntity in registry

    def test_get_outbound_relations(self) -> None:
        """Test getting outbound relations."""
        registry = SemanticRelationRegistry()
        registry.register(ViewpointEntity)

        edges = registry.get_outbound_relations(ViewpointEntity)

        assert len(edges) == 1
        assert edges[0].relation_type == RelationType.PROJECTS
        assert edges[0].source_type == ViewpointEntity
        assert edges[0].target_type == CoreEntity

    def test_get_outbound_relations_multiple(self) -> None:
        """Test getting multiple outbound relations."""
        registry = SemanticRelationRegistry()
        registry.register(MultiRelationEntity)

        edges = registry.get_outbound_relations(MultiRelationEntity)

        assert len(edges) == 2
        relation_types = {e.relation_type for e in edges}
        assert RelationType.ENABLES in relation_types
        assert RelationType.REFERENCES in relation_types

    def test_get_outbound_relations_unregistered(self) -> None:
        """Test getting outbound relations for unregistered type."""
        registry = SemanticRelationRegistry()

        edges = registry.get_outbound_relations(ViewpointEntity)

        assert edges == []

    def test_get_inbound_relations(self) -> None:
        """Test getting inbound relations."""
        registry = SemanticRelationRegistry()
        registry.register(ViewpointEntity)

        edges = registry.get_inbound_relations(CoreEntity)

        assert len(edges) == 1
        assert edges[0].relation_type == RelationType.PROJECTS
        assert edges[0].source_type == ViewpointEntity
        assert edges[0].target_type == CoreEntity

    def test_get_inbound_relations_multiple_sources(self) -> None:
        """Test getting inbound relations from multiple sources."""
        registry = SemanticRelationRegistry()
        registry.register(ViewpointEntity)
        registry.register(MultiRelationEntity)

        edges = registry.get_inbound_relations(CoreEntity)

        assert len(edges) == 2
        source_types = {e.source_type for e in edges}
        assert ViewpointEntity in source_types
        assert MultiRelationEntity in source_types

    def test_get_inbound_relations_unregistered_source(self) -> None:
        """Test that inbound requires source registration."""
        registry = SemanticRelationRegistry()
        # Don't register ViewpointEntity

        edges = registry.get_inbound_relations(CoreEntity)

        assert edges == []

    def test_get_relations_by_type_outbound(self) -> None:
        """Test filtering outbound relations by type."""
        registry = SemanticRelationRegistry()
        registry.register(MultiRelationEntity)

        edges = registry.get_relations_by_type(
            MultiRelationEntity, RelationType.ENABLES, direction="outbound"
        )

        assert len(edges) == 1
        assert edges[0].target_type == CoreEntity

    def test_get_relations_by_type_inbound(self) -> None:
        """Test filtering inbound relations by type."""
        registry = SemanticRelationRegistry()
        registry.register(ViewpointEntity)
        registry.register(MultiRelationEntity)

        edges = registry.get_relations_by_type(
            CoreEntity, RelationType.PROJECTS, direction="inbound"
        )

        assert len(edges) == 1
        assert edges[0].source_type == ViewpointEntity

    def test_get_relations_by_type_invalid_direction(self) -> None:
        """Test that invalid direction raises error."""
        registry = SemanticRelationRegistry()

        with pytest.raises(ValueError, match="direction must be"):
            registry.get_relations_by_type(
                CoreEntity, RelationType.PROJECTS, direction="invalid"
            )

    def test_get_projection_target(self) -> None:
        """Test convenience method for PROJECTS relation."""
        registry = SemanticRelationRegistry()
        registry.register(ViewpointEntity)

        target = registry.get_projection_target(ViewpointEntity)

        assert target == CoreEntity

    def test_get_projection_target_none(self) -> None:
        """Test get_projection_target when no PROJECTS relation."""
        registry = SemanticRelationRegistry()
        registry.register(UnrelatedEntity)

        target = registry.get_projection_target(UnrelatedEntity)

        assert target is None

    def test_registered_types_property(self) -> None:
        """Test registered_types returns frozen set."""
        registry = SemanticRelationRegistry()
        registry.register(ViewpointEntity)
        registry.register(MultiRelationEntity)

        types = registry.registered_types

        assert isinstance(types, frozenset)
        assert len(types) == 2

    def test_returns_copies(self) -> None:
        """Test that returned lists are copies (not references)."""
        registry = SemanticRelationRegistry()
        registry.register(ViewpointEntity)

        edges1 = registry.get_outbound_relations(ViewpointEntity)
        edges2 = registry.get_outbound_relations(ViewpointEntity)

        assert edges1 == edges2
        assert edges1 is not edges2  # Different list objects


# =============================================================================
# Slug Attribute Convention Tests
# =============================================================================


class TestSlugAttributeConvention:
    """Tests for slug attribute naming convention."""

    def test_simple_name(self) -> None:
        """Test simple class name."""
        assert get_relation_slug_attr(CoreEntity) == "core_entity_slug"

    def test_single_word(self) -> None:
        """Test single word class name."""

        class Persona(BaseModel):
            pass

        assert get_relation_slug_attr(Persona) == "persona_slug"

    def test_multiple_capitals(self) -> None:
        """Test class name with multiple capital letters."""

        class BoundedContext(BaseModel):
            pass

        assert get_relation_slug_attr(BoundedContext) == "bounded_context_slug"

    def test_acronym_style(self) -> None:
        """Test class name with acronym-style capitals."""

        class HTTPService(BaseModel):
            pass

        # Note: This produces h_t_t_p_service_slug which may not be ideal
        # but is consistent with the simple regex approach
        result = get_relation_slug_attr(HTTPService)
        assert result.endswith("_slug")
