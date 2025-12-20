# Enhancement Proposal: C4 Inference from Clean Architecture Idioms

## Summary

Extend the Julee documentation extensions to automatically infer C4 architectural
elements from clean architecture conventions, and unify HCD and C4 concepts where
they represent the same underlying reality. Rather than maintaining separate
definitions for personas/actors, accelerators/containers, and integrations/external
systems, a single definition should serve both documentation perspectives.

## Motivation

Julee solutions follow strict conventions (ADR 001) that encode architectural
intent in directory structure and code organisation:

- Bounded contexts as top-level packages in `src/`
- Domain layer with models, repository protocols, service protocols
- Use cases as application business rules
- Infrastructure with the three-layer Temporal pattern
- Apps directory with api, cli, worker entry points

These conventions are **already C4 information** expressed in a different form.
Manually transcribing this into C4 documentation creates:

1. **Duplication** - The same architectural facts exist in two places
2. **Drift risk** - Code changes but C4 docs don't get updated
3. **Effort** - Writing C4 definitions for well-structured code feels redundant

The principle from ADR 003 (sphinx-hcd) applies here: *"documentation that is
DRY, derives from authoritative sources, and reflects code reality."*

## Concept Unification

### The Problem with Separate Models

Currently, HCD and C4 maintain parallel concepts:

| HCD Concept | C4 Concept | Reality |
|-------------|------------|---------|
| Persona | Person/Actor | Same: a type of user |
| Application | Container | Same: an entry point |
| Accelerator | Container | Same: a bounded context |
| Integration | External System | Same: external dependency |

Maintaining these separately means:
- Defining the same thing twice in different vocabularies
- Risk of inconsistency between perspectives
- Extra work for documentation authors

### Unified Model Proposal

Instead of a "bridge" between HCD and C4, **unify the underlying model**:

```
                    ┌─────────────────┐
                    │  Unified Model  │
                    │                 │
                    │  - Person       │
                    │  - Container    │
                    │  - Component    │
                    │  - Relationship │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │   HCD    │  │    C4    │  │   Code   │
        │   View   │  │   View   │  │   View   │
        │          │  │          │  │          │
        │ Personas │  │  Actors  │  │ Protocols│
        │ Journeys │  │ Diagrams │  │ Classes  │
        │ Stories  │  │ Levels   │  │ Imports  │
        └──────────┘  └──────────┘  └──────────┘
```

A single `define-persona::` directive creates an entity that appears as:
- A **Persona** in HCD documentation (journeys, stories, epics)
- An **Actor** in C4 system context diagrams
- A **User type** in requirements traceability

### Specific Unifications

#### Persona = C4 Person

HCD personas are the subjects of stories and journeys. C4 Person elements are
actors who interact with software systems. **They are the same concept.**

```rst
.. define-persona:: solutions-developer
   :name: Solutions Developer
   :goals:
      Build reliable workflow solutions

   A developer building production systems with Julee.
```

This single definition should:
- Appear in HCD persona indexes and journey diagrams
- Appear as an actor in C4 system context diagrams
- Link stories to the C4 components that satisfy them

#### Application = C4 Container (Entry Point)

HCD applications are entry points exposing features to personas. C4 containers
are deployable units. **An application IS a container.**

```rst
.. define-app:: staff-portal
   :type: api
   :personas: Knowledge Curator, Solutions Developer
```

Should automatically create a C4 container with:
- Technology inferred from type (api → FastAPI, cli → Typer, worker → Temporal)
- Relationships to personas (actors use this container)
- Relationships to accelerators it depends on

#### Accelerator = C4 Container (Bounded Context)

HCD accelerators are bounded contexts with pipelines. C4 containers are
separately deployable units. **An accelerator IS a container.**

The existing `define-accelerator::` directive already does code introspection.
This should additionally:
- Register a C4 container
- Populate components from introspected entities, use cases, protocols
- Infer relationships from import analysis

#### Integration = C4 External System

HCD integrations document external system connections. C4 external systems are
things outside the system boundary. **They are the same.**

```rst
.. define-integration:: temporal-cloud
   :type: workflow-orchestration
   :direction: outbound
```

Should create both an HCD integration AND a C4 external system.

## Idiom Refinements

To better support inference and unification, consider refining the conventions:

### 1. Explicit Container Type in Accelerators

Add a container classification to accelerators:

```rst
.. define-accelerator:: vocabulary
   :container-type: bounded-context
   :technology: Python
```

Or infer from directory structure:
- `src/{name}/` with domain/ → bounded-context container
- `apps/api/` → api container
- `apps/worker/` → worker container

### 2. Persona References Create Relationships

When a story references a persona and an app:

```rst
.. define-story:: upload-document
   :persona: Knowledge Curator
   :app: staff-portal
```

This implies a C4 relationship: `Knowledge Curator → uses → staff-portal`

### 3. App-Accelerator Dependencies

When an app declares accelerator dependencies:

```yaml
# apps/staff-portal/app.yaml
accelerators:
  - vocabulary
  - assessment
```

This implies C4 relationships: `staff-portal → uses → vocabulary`

### 4. Service Protocols Imply External Systems

Classes in `domain/services/` that wrap external APIs could be parsed to
discover external system dependencies:

```python
# domain/services/anthropic.py
class AnthropicService(Protocol):
    """Client for Anthropic Claude API."""
```

Implies external system: `Anthropic Claude API`

### 5. Standard Naming Conventions

Strengthen naming conventions to improve inference:

| Convention | Inferred As |
|------------|-------------|
| `*Repository` protocol | Data store component |
| `*Service` protocol | External service component |
| `*UseCase` class | Business logic component |
| `*Pipeline` class | Workflow component |

## Inferred C4 Elements

### From Directory Structure

```
Clean Architecture          →  C4 Model
─────────────────────────────────────────────────────
Solution repository         →  Software System
apps/api/                   →  Container (API)
apps/cli/                   →  Container (CLI)
apps/worker/                →  Container (Worker)
src/{bounded-context}/      →  Container (per domain)
```

### From AST Introspection

```
Code Structure              →  C4 Components
─────────────────────────────────────────────────────
domain/models/ classes      →  Entity Components
use_cases/ classes          →  Use Case Components
domain/repositories/        →  Protocol Components
domain/services/            →  Protocol Components
worker/pipelines/           →  Pipeline Components
```

### From Import Analysis

```
Import Pattern              →  C4 Relationship
─────────────────────────────────────────────────────
UseCase imports Repository  →  "reads from / writes to"
UseCase imports Service     →  "uses"
Pipeline imports UseCase    →  "executes"
API route imports UseCase   →  "exposes"
```

### From HCD Entities

```
HCD Declaration             →  C4 Element
─────────────────────────────────────────────────────
define-persona::            →  Person (actor)
define-app::                →  Container (entry point)
define-accelerator::        →  Container (bounded context)
define-integration::        →  External System
story :persona: :app:       →  Relationship (uses)
```

## Implementation Approach

### Shared Domain Model

Create unified domain models that serve both perspectives:

```python
class Person(BaseModel):
    """Unified person/persona model."""
    slug: str
    name: str
    # HCD attributes
    goals: list[str]
    frustrations: list[str]
    jobs_to_be_done: list[str]
    # C4 attributes
    is_external: bool = True  # C4: external actor

class Container(BaseModel):
    """Unified container model."""
    slug: str
    name: str
    # Classification
    container_type: Literal["api", "cli", "worker", "bounded-context"]
    technology: str
    # HCD attributes (if bounded-context)
    pipelines: list[str]
    # C4 attributes
    components: list[Component]
```

### Single Directive, Multiple Views

Each directive populates the unified model:

```rst
.. define-persona:: knowledge-curator
   :name: Knowledge Curator
   :goals: Build comprehensive vocabulary
```

The persona appears in:
- `persona-index::` (HCD view)
- `system-context-diagram::` (C4 view)
- `journeys-for-persona::` (HCD view)

### Inference Directives

For elements that can be fully inferred:

```rst
.. infer-containers::
   :from: apps/, src/

.. infer-components::
   :container: vocabulary

.. infer-relationships::
   :scope: vocabulary
```

### Hybrid Mode

Allow explicit definitions to supplement or override inference:

```rst
.. infer-external-systems::
   :from: docker-compose, service-protocols

.. define-external-system:: legacy-mainframe
   :description: Not discoverable, must be explicit
```

## Open Questions

### Unified vs Federated Model

Should HCD and C4 share a single repository, or have separate repositories
with cross-references?

- **Unified**: Simpler, guarantees consistency
- **Federated**: More flexible, allows independent evolution

### Inference Completeness

Import analysis may miss:
- Dependency injection (runtime wiring)
- Dynamic imports
- Configuration-driven relationships

Options:
- Accept incompleteness, allow manual supplementation
- Parse DI container configuration
- Warn about gaps

### Diagram Layout

C4 diagrams need spatial layout. Options:
- Auto-layout (PlantUML default)
- Hint-based layout (suggest positions)
- Manual layout with inferred content

### Granularity of Components

How deep should component inference go?
- Just top-level classes?
- Include methods as sub-components?
- Include class relationships?

## Success Criteria

1. **Single source of truth**: Define once, appear in both HCD and C4 views
2. **Automatic inference**: Well-structured code needs minimal explicit C4
3. **Consistency guaranteed**: Cannot have persona without corresponding actor
4. **Progressive detail**: System context auto-generated, component diagrams
   can be elaborated manually
5. **Traceability**: Navigate from persona → story → component → code

## Next Steps

1. **Discuss unification approach** - unified vs federated model
2. **Prototype persona unification** - single definition, dual rendering
3. **Extend accelerator directive** - add C4 container generation
4. **Design inference directives** - API for automatic discovery

## References

- ADR 001 (julee): Contrib Module Layout
- ADR 003 (julee): Sphinx HCD Extensions Package
- [C4 Model](https://c4model.com/) - Simon Brown
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) - Robert C. Martin
