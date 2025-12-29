"""SemanticRelation doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from enum import Enum

import pytest
from pydantic import BaseModel, ValidationError

from julee.core.decorators import get_semantic_relations, semantic_relation
from julee.core.entities.semantic_relation import (
    EntityType,
    RelationType,
    SemanticRelation,
)


class TestSemanticRelationEntityTypes:
    """Doctrine about SemanticRelation type constraints."""

    def test_source_type_MUST_be_BaseModel_or_Enum_subclass(self):
        """SemanticRelation.source_type MUST be a BaseModel or Enum subclass.

        This ensures semantic relations only connect doctrine-valid entity types.
        Plain classes, dataclasses, or other types are not permitted.
        """

        class ValidEntity(BaseModel):
            name: str

        class ValidEnum(str, Enum):
            A = "a"

        # Valid: BaseModel subclass
        rel = SemanticRelation(
            source_type=ValidEntity,
            target_type=ValidEntity,
            relation_type=RelationType.IS_A,
        )
        assert rel.source_type is ValidEntity

        # Valid: Enum subclass
        rel = SemanticRelation(
            source_type=ValidEnum,
            target_type=ValidEntity,
            relation_type=RelationType.IS_A,
        )
        assert rel.source_type is ValidEnum

    def test_target_type_MUST_be_BaseModel_or_Enum_subclass(self):
        """SemanticRelation.target_type MUST be a BaseModel or Enum subclass.

        This ensures semantic relations only connect doctrine-valid entity types.
        Plain classes, dataclasses, or other types are not permitted.
        """

        class ValidEntity(BaseModel):
            name: str

        class ValidEnum(str, Enum):
            A = "a"

        # Valid: BaseModel subclass as target
        rel = SemanticRelation(
            source_type=ValidEntity,
            target_type=ValidEntity,
            relation_type=RelationType.PROJECTS,
        )
        assert rel.target_type is ValidEntity

        # Valid: Enum subclass as target
        rel = SemanticRelation(
            source_type=ValidEntity,
            target_type=ValidEnum,
            relation_type=RelationType.RELATED,
        )
        assert rel.target_type is ValidEnum

    def test_types_MUST_be_actual_types_not_strings(self):
        """SemanticRelation types MUST be actual type objects, not string names.

        Type references as strings would break introspection and validation.
        Using actual types ensures relationships are verifiable at import time.
        """

        class ValidEntity(BaseModel):
            name: str

        # Valid: actual type
        rel = SemanticRelation(
            source_type=ValidEntity,
            target_type=ValidEntity,
            relation_type=RelationType.IS_A,
        )
        assert isinstance(rel.source_type, type)
        assert isinstance(rel.target_type, type)

        # Invalid: string type name would be caught by Pydantic validation
        with pytest.raises(ValidationError):
            SemanticRelation(
                source_type="ValidEntity",  # type: ignore[arg-type]
                target_type=ValidEntity,
                relation_type=RelationType.IS_A,
            )


class TestSemanticRelationDecorator:
    """Doctrine about the semantic_relation decorator."""

    def test_decorated_class_MUST_retain_semantic_relations(self):
        """Classes decorated with @semantic_relation MUST retain the relation.

        The decorator attaches a __semantic_relations__ attribute to the class
        containing all declared relations. This enables introspection.
        """

        class TargetEntity(BaseModel):
            slug: str

        @semantic_relation(TargetEntity, RelationType.IS_A)
        class SourceEntity(BaseModel):
            name: str

        relations = get_semantic_relations(SourceEntity)
        assert len(relations) == 1
        assert relations[0].source_type is SourceEntity
        assert relations[0].target_type is TargetEntity
        assert relations[0].relation_type == RelationType.IS_A

    def test_multiple_relations_on_same_class_MUST_all_be_retained(self):
        """Multiple @semantic_relation decorators on a class MUST all be retained.

        A class may have multiple semantic relations (e.g., is_a Persona AND
        enables Story). All must be discoverable.
        """

        class EntityA(BaseModel):
            slug: str

        class EntityB(BaseModel):
            slug: str

        @semantic_relation(EntityA, RelationType.IS_A)
        @semantic_relation(EntityB, RelationType.ENABLES)
        class MultiRelationEntity(BaseModel):
            name: str

        relations = get_semantic_relations(MultiRelationEntity)
        assert len(relations) == 2

        # Order is reversed due to decorator stacking (innermost first)
        types = {(r.target_type, r.relation_type) for r in relations}
        assert (EntityA, RelationType.IS_A) in types
        assert (EntityB, RelationType.ENABLES) in types

    def test_undecorated_class_MUST_return_empty_relations(self):
        """Undecorated classes MUST return empty list from get_semantic_relations.

        This ensures safe introspection without checking for attribute existence.
        """

        class PlainEntity(BaseModel):
            name: str

        relations = get_semantic_relations(PlainEntity)
        assert relations == []


class TestRelationTypeValues:
    """Doctrine about RelationType enum values."""

    def test_RelationType_MUST_include_standard_relation_types(self):
        """RelationType MUST include IS_A, PROJECTS, IMPLEMENTS, and ENABLES.

        These are the core semantic relationships used across the framework:
        - IS_A: specialization/instance (CustomerSegment is_a Persona)
        - PROJECTS: view/projection (Accelerator projects BoundedContext)
        - IMPLEMENTS: protocol implementation (SqlRepo implements RepoProtocol)
        - ENABLES: supports/enables (UseCase enables Story)
        """
        assert RelationType.IS_A.value == "is_a"
        assert RelationType.PROJECTS.value == "projects"
        assert RelationType.IMPLEMENTS.value == "implements"
        assert RelationType.ENABLES.value == "enables"

    def test_RelationType_MAY_include_SKOS_relations(self):
        """RelationType MAY include SKOS vocabulary relations.

        BROADER, NARROWER, and RELATED support knowledge organization:
        - BROADER: target is more general (Vehicle broader TransportMode)
        - NARROWER: target is more specific
        - RELATED: associative, non-hierarchical
        """
        assert RelationType.BROADER.value == "broader"
        assert RelationType.NARROWER.value == "narrower"
        assert RelationType.RELATED.value == "related"


class TestSemanticRelationProperties:
    """Doctrine about SemanticRelation computed properties."""

    def test_source_name_MUST_be_fully_qualified(self):
        """SemanticRelation.source_name MUST return fully qualified type name.

        Format: module.ClassName (e.g., julee.hcd.entities.persona.Persona)
        """

        class LocalEntity(BaseModel):
            name: str

        rel = SemanticRelation(
            source_type=LocalEntity,
            target_type=LocalEntity,
            relation_type=RelationType.IS_A,
        )
        assert rel.source_name == f"{LocalEntity.__module__}.{LocalEntity.__name__}"
        assert "LocalEntity" in rel.source_name

    def test_target_name_MUST_be_fully_qualified(self):
        """SemanticRelation.target_name MUST return fully qualified type name.

        Format: module.ClassName (e.g., julee.core.entities.bounded_context.BoundedContext)
        """

        class LocalEntity(BaseModel):
            name: str

        rel = SemanticRelation(
            source_type=LocalEntity,
            target_type=LocalEntity,
            relation_type=RelationType.PROJECTS,
        )
        assert rel.target_name == f"{LocalEntity.__module__}.{LocalEntity.__name__}"
        assert "LocalEntity" in rel.target_name
