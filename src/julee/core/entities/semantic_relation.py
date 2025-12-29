"""SemanticRelation entity for declaring relationships between entity types.

Enables explicit declaration of how entities across bounded contexts relate
semantically - particularly how solution entities map to framework viewpoint
entities, and how viewpoint entities project onto core entities.

This supports the dependency model:
- Core is self-contained, knows only itself
- Viewpoints depend on core, know how their entities project onto core
- Solutions depend on framework, know how their entities relate to framework

Example usage with the semantic_relation decorator:

    from julee.core.decorators import semantic_relation
    from julee.core.entities.semantic_relation import RelationType
    from julee.hcd.entities import Persona

    @semantic_relation(Persona, RelationType.IS_A)
    class CustomerSegment(BaseModel):
        '''A customer segment - is_a Persona in HCD terms.'''
        slug: str
        name: str
"""

from enum import Enum
from typing import Type

from pydantic import BaseModel


class RelationType(str, Enum):
    """Semantic relationship types between entity types.

    Inspired by SKOS (Simple Knowledge Organization System) relationship
    vocabulary, adapted for framework entity relationships.
    """

    IS_A = "is_a"
    """Instance of / specialization relationship.

    The source type IS A specific instance or specialization of the target.
    Example: CustomerSegment is_a Persona
    """

    PROJECTS = "projects"
    """View onto / projection relationship.

    The source type provides a view or projection of the target.
    Example: Accelerator projects BoundedContext
    """

    IMPLEMENTS = "implements"
    """Protocol implementation relationship.

    The source type implements the protocol defined by the target.
    Example: SqlAlchemyUserRepo implements UserRepository
    """

    ENABLES = "enables"
    """Enables / supports relationship.

    The source type enables or supports the functionality of the target.
    Example: AuthenticationUseCase enables Story
    """

    BROADER = "broader"
    """Broader concept relationship (SKOS).

    The target is a broader/more general concept than the source.
    Example: Vehicle broader TransportMode
    """

    NARROWER = "narrower"
    """Narrower concept relationship (SKOS).

    The target is a narrower/more specific concept than the source.
    Example: TransportMode narrower Vehicle
    """

    RELATED = "related"
    """Associative relationship.

    The source and target are related but without hierarchical implication.
    """


# Type alias for doctrine-valid entity types.
# Valid types are Pydantic BaseModel subclasses or Enum subclasses.
EntityType = Type[BaseModel] | Type[Enum]


class SemanticRelation(BaseModel):
    """A semantic relationship between two entity types.

    First-class domain entity representing how concepts relate across
    bounded contexts and framework layers. Used for:

    - Declaring how solution entities map to framework viewpoint entities
    - Declaring how viewpoint entities project onto core entities
    - Enabling introspection for documentation generation
    - Validating architectural consistency

    The source_type and target_type must be valid entity types as defined
    by doctrine: BaseModel subclasses or Enum subclasses.
    """

    source_type: EntityType
    """The entity type declaring the relationship."""

    target_type: EntityType
    """The entity type being related to."""

    relation_type: RelationType
    """The type of semantic relationship."""

    model_config = {"arbitrary_types_allowed": True}

    @property
    def source_name(self) -> str:
        """Fully qualified name of the source type."""
        return f"{self.source_type.__module__}.{self.source_type.__name__}"

    @property
    def target_name(self) -> str:
        """Fully qualified name of the target type."""
        return f"{self.target_type.__module__}.{self.target_type.__name__}"

    def __repr__(self) -> str:
        """Human-readable representation."""
        return (
            f"SemanticRelation({self.source_type.__name__} "
            f"{self.relation_type.value} {self.target_type.__name__})"
        )
