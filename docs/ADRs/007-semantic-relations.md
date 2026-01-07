# ADR 007: Semantic Relations Decorator Pattern

## Status

Draft

## Date

2026-01-07

## Context

Julee solutions consist of multiple bounded contexts, each with their own entities. These entities often have meaningful relationships across bounded context boundaries:

- A `Story` in the HCD bounded context relates to a `UseCase` in core
- An `Accelerator` provides a view onto a `BoundedContext`
- A solution's `CustomerSegment` entity specializes the framework's `Persona`

These relationships are **semantic** - they express architectural intent and domain meaning, not just runtime data flow. They differ from:

1. **Import dependencies** - which are compile-time coupling
2. **Foreign key relationships** - which are instance-level data references
3. **Event subscriptions** - which are runtime behavior coupling

Without explicit semantic relationships:

- Documentation cannot show cross-BC navigation (e.g., "what relates to UseCase?")
- Architectural validation cannot verify that entities properly declare their intent
- Introspection tools cannot discover how bounded contexts conceptually relate

## Decision

Entity types SHALL declare semantic relationships to other entity types in other bounded contexts, **where those semantic relationships cannot otherwise be inferred by AST/code analysis**. The `@semantic_relation` decorator attaches relationship metadata to classes, discoverable via introspection.

### The Decorator

```python
from julee.core.decorators import semantic_relation
from julee.core.entities.semantic_relation import RelationType

@semantic_relation("julee.hcd.entities.app.App", RelationType.PART_OF)
@semantic_relation("julee.hcd.entities.persona.Persona", RelationType.REFERENCES)
@semantic_relation("julee.core.entities.use_case.UseCase", RelationType.PROJECTS)
class Story(BaseModel):
    """A user story - part of an App, references a Persona, projects a UseCase."""
    slug: str
    persona: str
    app_slug: str
```

The decorator accepts:
- **target_type**: The entity type to relate to (string path for circular imports, or direct type)
- **relation**: A `RelationType` enum value expressing the relationship semantics

### RelationType Vocabulary

The relationship vocabulary is inspired by SKOS (Simple Knowledge Organization System), extended for framework needs:

| Type | Meaning | Example |
|------|---------|---------|
| `IS_A` | Specialization/instance | CustomerSegment is_a Persona |
| `PROJECTS` | View/projection onto | Accelerator projects BoundedContext |
| `IMPLEMENTS` | Protocol implementation | SqlAlchemyRepo implements Repository |
| `ENABLES` | Supports/enables | AuthUseCase enables Story |
| `PART_OF` | Contained within | Story part_of App |
| `CONTAINS` | Aggregates | Epic contains Story |
| `REFERENCES` | Non-owning reference | Story references Persona |
| `BROADER` | More general (SKOS) | Vehicle broader TransportMode |
| `NARROWER` | More specific (SKOS) | TransportMode narrower Vehicle |
| `RELATED` | Associative | Generic relationship |

### SemanticRelation Entity

Relationships are stored as first-class domain entities:

```python
class SemanticRelation(BaseModel):
    """A semantic relationship between two entity types."""

    source_type: EntityType  # BaseModel or Enum subclass
    target_type: EntityType
    relation_type: RelationType
```

The decorator populates a `__semantic_relations__` attribute on decorated classes:

```python
from julee.core.decorators import get_semantic_relations

relations = get_semantic_relations(Story)
# [SemanticRelation(Story PART_OF App),
#  SemanticRelation(Story REFERENCES Persona),
#  SemanticRelation(Story PROJECTS UseCase)]
```

### SemanticRelationRegistry Service

A registry service indexes registered types for bidirectional traversal:

```python
registry = SemanticRelationRegistry()
registry.register(Story)
registry.register(Epic)
registry.register(App)

# Forward: what does Story relate to?
outbound = registry.get_outbound_relations(Story)
# [RelationEdge(PART_OF, Story, App), ...]

# Reverse: what relates to UseCase?
inbound = registry.get_inbound_relations(UseCase)
# [RelationEdge(PROJECTS, Story, UseCase)]
```

This enables infrastructure (documentation, introspection) to navigate the relationship graph in both directions without hardcoding entity-to-entity mappings.

### Relation Labels for Documentation

Each relation type has forward and inverse labels for human-readable documentation:

| RelationType | Forward Label | Inverse Label |
|--------------|---------------|---------------|
| `PROJECTS` | "Projects" | "Projected by" |
| `ENABLES` | "Enables" | "Enabled by" |
| `REFERENCES` | "References" | "Referenced by" |
| `PART_OF` | "Part of" | "Contains" |
| `CONTAINS` | "Contains" | "Part of" |

### String References for Circular Imports

When entities have circular import relationships, use string paths:

```python
# In story.py - cannot import App directly due to circular import
@semantic_relation("julee.hcd.entities.app.App", RelationType.PART_OF)
class Story(BaseModel):
    ...
```

The string is resolved to an actual type at decoration time via dynamic import.

### Doctrine Constraints

Semantic relations are subject to doctrine:

1. **source_type and target_type MUST be BaseModel or Enum subclasses** - only doctrine-valid entity types can participate in semantic relations

2. **Types MUST be actual types, not strings** - the SemanticRelation entity stores resolved types, not string references

3. **Multiple relations on one class MUST all be retained** - decorator stacking is supported

4. **Undecorated classes MUST return empty relations** - safe introspection via `get_semantic_relations()`

## Consequences

### Positive

1. **Cross-BC navigation** - Documentation can generate bidirectional links between related entities across bounded contexts

2. **Architectural validation** - Doctrine tests can verify that entities declare appropriate semantic relationships

3. **Introspection support** - Tools can discover the conceptual graph of entity relationships

4. **Separation from runtime** - Semantic relations express architectural intent without creating runtime coupling

5. **Vocabulary consistency** - Standard relation types ensure consistent meaning across the framework

6. **Invertible relations** - Registry enables both "what does X relate to?" and "what relates to X?"

### Negative

1. **Declaration overhead** - Entities must explicitly declare their semantic relationships

2. **String paths for circulars** - Circular imports require less-readable string paths

3. **Registry population** - Infrastructure must register types before querying relations

### Neutral

1. **Decorator stacking order** - Multiple decorators stack in reverse order (innermost first), which is standard Python behavior

## Implementation

### Core Components

- `julee/core/decorators.py` - `@semantic_relation` decorator and `get_semantic_relations()` helper
- `julee/core/entities/semantic_relation.py` - `SemanticRelation` entity and `RelationType` enum
- `julee/core/services/semantic_relation_registry.py` - `SemanticRelationRegistry` service

### Doctrine Tests

- `julee/core/doctrine/test_semantic_relation.py` - Doctrine tests for semantic relation constraints

### Usage in Framework

The HCD bounded context uses semantic relations extensively:
- `Story` → App (PART_OF), Persona (REFERENCES), UseCase (PROJECTS)
- `Epic` → Story (CONTAINS)
- `Accelerator` → BoundedContext (PROJECTS)

## Alternatives Considered

### 1. Class Attributes Instead of Decorators

Define relations as class attributes:

```python
class Story(BaseModel):
    __semantic_relations__ = [
        ("julee.hcd.entities.app.App", "part_of"),
    ]
```

**Rejected**: Less readable, no type checking, inconsistent with Python conventions for metadata.

### 2. External Mapping File

Define relations in a separate YAML/JSON file:

```yaml
Story:
  - target: App
    relation: part_of
```

**Rejected**: Separates declaration from entity, easy to get out of sync, not discoverable via introspection.

### 3. Runtime Event Subscriptions

Infer relations from which events entities subscribe to.

**Rejected**: Semantic relations express architectural intent, not runtime behavior. Many semantic relationships have no runtime manifestation.

### 4. Import Graph Analysis

Infer relations from import statements.

**Rejected**: Import dependencies are about code coupling, not semantic meaning. An entity may import another for validation without having a semantic relationship.

## References

- [SKOS Simple Knowledge Organization System](https://www.w3.org/2004/02/skos/)
- [ADR 002: Doctrine Test Architecture](./002-doctrine-test-architecture.md)
- Issue #63: ADR needed: Semantic Relations Decorator Pattern
