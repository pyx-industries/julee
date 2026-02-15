# Julee Architecture Overview

Julee is a Python framework for building resilient, auditable business
processes using Temporal workflows. It implements Clean Architecture with
strict opinions about code organisation, enforced by executable tests
rather than prose documentation.

This document synthesises the architectural decisions, patterns, and
conventions that govern Julee solutions.


## Organising Principle: Screaming Architecture

A Julee solution is organised around bounded contexts -- the distinct
areas of a business domain. When you open `src/`, the directory names
scream what the system does, not what frameworks it uses:

```
src/
  billing/          # Bounded context
    entities/
    use_cases/
    repositories/
    services/
    infrastructure/
    tests/
  compliance/       # Bounded context
    entities/
    use_cases/
    ...
  apps/             # Application entry points (not a bounded context)
    api/
    cli/
    worker/
```

The framework itself follows the same convention. Its bounded contexts
happen to be software architecture concepts:

| Bounded Context | Domain |
|-----------------|--------|
| `core`          | Framework vocabulary: Entity, UseCase, Pipeline, Repository, Service |
| `hcd`           | Human-Centred Design: Persona, Journey, Epic, Story, Accelerator |
| `c4`            | C4 Architecture: SoftwareSystem, Container, Component, Relationship |
| `supply_chain`  | Supply chain provenance: Party, semantic relations |
| `contrib/ceap`  | Capture-Extract-Assemble-Publish workflow pattern |
| `contrib/polling`| Endpoint polling and change detection |
| `contrib/untp`  | UN Transparency Protocol vocabulary mapping |


## The Dependency Rule

Source code dependencies point inward. Always. The inner layers know
nothing about the outer layers.

```
                    ┌─────────────────────┐
                    │      Entities       │  Pure business concepts
                    │  (know nothing)     │
                    ├─────────────────────┤
                    │  Repositories (P)   │  Persistence protocols
                    │  Services (P)       │  External service protocols
                    │  Use Cases          │  Application business rules
                    ├─────────────────────┤
                    │   Infrastructure    │  Implementations
                    ├─────────────────────┤
                    │    Applications     │  Entry points (API, CLI, Worker)
                    └─────────────────────┘
```

The layers and their import rules are codified in
`julee.core.doctrine_constants`:

| Layer | May Import From | Must Not Import From |
|-------|----------------|---------------------|
| `entities/` | Standard library, Pydantic | Everything else |
| `use_cases/` | entities, repositories (protocols), services (protocols) | infrastructure, apps |
| `repositories/` | entities | infrastructure, apps |
| `services/` | entities | infrastructure, apps |
| `infrastructure/` | Everything inward | apps |
| `apps/` | Everything inward | -- |


## Bounded Context Structure

Every bounded context follows a flat layout. There is no nested
`domain/` directory -- the layers sit directly under the context:

```
{bounded_context}/
  entities/           # Domain models (Pydantic BaseModel)
  repositories/       # Repository protocols (typing.Protocol)
  services/           # Service protocols (typing.Protocol)
  use_cases/          # Application business rules
  infrastructure/     # Implementations of protocols
    repositories/     #   Concrete repository classes
    services/         #   Concrete service classes
    handlers/         #   Handler implementations
  apps/               # Entry points (optional, for standalone deployment)
    api/
    cli/
    worker/
  tests/              # Co-located test suite
```

A bounded context must have at least `entities/` or `use_cases/` to be
recognised by the framework's discovery mechanism. Everything else is
optional and added as needed.


## Core Architectural Concepts

### Entities

Entities are domain concepts that define the ontology of a bounded
context. They are the most stable part of the architecture -- they
represent the business itself, not the technology serving it.

All entities inherit from `pydantic.BaseModel`. Entity class names must
be PascalCase and must not end with `UseCase`, `Request`, or `Response`.

### Use Cases

Use cases are application-specific business rules. Each use case is a
complete, independent operation: "Create a Journey", "Validate a
Document", "Detect New Data". The `execute()` method is the single
entry point, taking a `Request` and returning a `Response`.

```python
class CreateJourneyUseCase:
    def __init__(
        self,
        journey_repo: JourneyRepository,     # Protocol, not implementation
        persona_repo: PersonaRepository,
        clock_service: ClockService,
    ):
        ...

    async def execute(self, request: CreateJourneyRequest) -> CreateJourneyResponse:
        # Business logic here -- no knowledge of HTTP, Temporal, or databases
        ...
```

Use cases depend on protocols, never implementations. They have no
knowledge of databases, APIs, or frameworks. Dependencies are injected
via the constructor; the DI container wires them at composition time.

### Request and Response

Requests carry input data across the boundary into use cases. Responses
carry output data back. Each use case has its own Request/Response pair.
Both inherit from `pydantic.BaseModel`.

At API boundaries (REST, MCP, CLI), the full DTO pattern is used with
dedicated Request/Response classes, validation, and domain model
conversion. For internal use cases called only from trusted code
(workflows, other use cases), primitive parameters may be used instead.

### Repository Protocols

Repositories store things. A repository protocol defines persistence
operations (`get`, `save`, `list`, `delete`) for a single entity type
without revealing how persistence works. The protocol lives in the
domain layer; implementations live in infrastructure.

```python
class JourneyRepository(Protocol):
    async def get(self, slug: str) -> Journey | None: ...
    async def save(self, entity: Journey) -> None: ...
    async def list_all(self) -> list[Journey]: ...
```

The distinguishing trait: a repository is bound to ONE entity type.

### Service Protocols

Services do things. A service protocol defines operations that transform
between two or more entity types -- calling an LLM, evaluating rules,
mapping ontologies. Like repositories, the protocol lives in the domain
layer; implementations live in infrastructure.

```python
class KnowledgeService(Protocol):
    async def extract(self, document: Document, config: ExtractionConfig) -> ExtractionResult: ...
```

The distinguishing trait: a service is bound to TWO or MORE entity types.

### Handler Services

When a use case recognises a domain condition that should trigger
further action, it hands off to a handler rather than computing next
steps itself (ADR 003). Handlers have domain-typed interfaces and return
`Acknowledgement` (wilco/roger semantics):

```python
class OrphanStoryHandler(Protocol):
    async def handle(self, story: Story) -> Acknowledgement: ...
```

The use case knows "if the story has no epic, give it to the
orphan-story-handler". It does not know what the handler does -- queue
work, send notifications, trigger another use case, or nothing.

Cross-bounded-context coordination uses the same pattern. The solution
provider creates a handler implementation that bridges two contexts at
composition time.


## Pipelines and Temporal

A pipeline is a use case wrapped for durable execution via Temporal.

```
Use Case (pure business logic)
    +
Temporal treatment (decorators, proxies)
    =
Pipeline (durable, reliable, observable)
```

All Julee pipelines are Temporal workflows, but not all Temporal
workflows are Julee pipelines. All Julee pipelines wrap Julee use cases,
but not all use cases are pipelines.

### Pipeline Proxies

When a use case runs as a pipeline, its repository and service
dependencies are replaced with proxy classes that route every method
call through a Temporal activity. The proxy implements the same protocol,
so the use case cannot tell the difference. But each call now has its
own timeout, retry policy, state persistence, and audit trail.

```python
# Direct execution: real repository
use_case = ExtractAssembleDataUseCase(
    document_repo=MinioDocumentRepository(client),
)

# Pipeline execution: proxy repository
use_case = ExtractAssembleDataUseCase(
    document_repo=WorkflowDocumentRepositoryProxy(),
)
```

### Pipeline Responsibilities

A pipeline does exactly three things:

1. Execute the wrapped use case with workflow-safe proxies
2. Consult a MultiplexRouter for downstream routes
3. Dispatch to matched downstream pipelines

A pipeline must not contain business logic, data transformation, or
conditional logic beyond "for each matched route, dispatch".

### Execution-Agnostic Use Cases (ADR 004)

Use cases are completely agnostic about their execution context. Time
is abstracted via `ClockService` (system clock in normal code, Temporal
deterministic clock in workflows). Execution identity is abstracted via
`ExecutionService` (UUID in normal code, workflow ID in Temporal). These
are injected like any other service dependency.

### MultiplexRouter

Routing from one pipeline to downstream pipelines is declarative.
Routes specify conditions on the response, a target pipeline, and field
mappings from response to request -- all as introspectable data, not
lambdas. The router can generate PlantUML visualisations from its
configuration.


## Applications

Applications are entry points that expose use cases to the outside
world. They are orthogonal to bounded contexts -- they compose and wire
contexts together rather than containing business logic.

| Application Type | Technology | How It Invokes Use Cases |
|-----------------|------------|------------------------|
| REST-API | FastAPI | Direct execution or dispatch via Temporal client |
| TEMPORAL-WORKER | Temporal SDK | Polls task queue, executes pipeline activities |
| CLI | Typer | Direct execution or dispatch via Temporal client |
| MCP | Model Context Protocol | Direct execution, exposing use cases to AI assistants |
| SPHINX-EXTENSION | Sphinx | Calls read use cases to render documentation |

Applications live at `{solution}/apps/` (a reserved directory that
cannot be a bounded context name). UIs interact exclusively through the
API -- they do not have direct access to use cases or repositories.


## Contrib Modules

Contrib modules are pre-built accelerators that ship with the framework
(ADR 001). Each follows the same bounded context structure as an
external solution. A contrib module can theoretically be extracted to
its own repository.

Current contrib modules:

- **CEAP** (`contrib/ceap`) -- Capture-Extract-Assemble-Publish
  workflow pattern for AI document processing
- **Polling** (`contrib/polling`) -- Endpoint polling with change
  detection and handler-based dispatch
- **UNTP** (`contrib/untp`) -- UN Transparency Protocol vocabulary
  projection layer

Solutions import from contrib modules and wire them into their own
applications:

```python
from julee.contrib.ceap import ExtractAssembleDataUseCase
from julee.contrib.polling import NewDataDetectionUseCase
```


## Doctrine and Policy (ADR 002, ADR 005)

### Doctrine

Doctrine is the set of architectural rules that all Julee solutions must
follow. The rules are expressed and enforced as pytest tests with RFC
2119 language (MUST, SHOULD, MAY). The test docstring IS the rule
statement; the test body IS the enforcement. There is no separate
specification that can drift from reality.

```python
class TestBoundedContextStructure:
    """Doctrine about bounded context structure."""

    async def test_bounded_context_MUST_have_entities_or_use_cases(self):
        """A bounded context MUST have entities/ or use_cases/."""
        ...
```

All naming conventions, layer constraints, and structural rules are
defined as constants in `julee.core.doctrine_constants`. Doctrine tests
reference these constants, making the rules discoverable and
machine-readable.

### Key Doctrine Rules

**Entities:**
- MUST be PascalCase
- MUST inherit from `BaseModel`
- MUST NOT end with `UseCase`, `Request`, or `Response`

**Use Cases:**
- MUST have an `execute()` method
- MUST have matching `Request` and `Response` classes (at API boundaries)
- MUST NOT import from infrastructure or apps

**Protocols:**
- MUST inherit from `typing.Protocol`
- Repository protocols live in `{bc}/repositories/`
- Service protocols live in `{bc}/services/`
- Implementations live in `{bc}/infrastructure/`

**Bounded Contexts:**
- MUST have `entities/` or `use_cases/`
- MUST NOT use reserved names (`apps`, `deployments`, `docs`)
- Are discovered automatically by filesystem introspection

**Pipelines:**
- MUST wrap exactly one use case
- MUST be decorated with `@workflow.defn`
- MUST NOT contain business logic
- Live at `{bc}/apps/worker/pipelines.py`

### Policy

Policy is distinct from doctrine (ADR 005). Doctrine is axiomatic and
universal -- it defines what Julee concepts ARE. Policy is strategic and
adoptable -- it represents choices about HOW to implement solutions.

Solutions declare themselves as Julee solutions via `[tool.julee]` in
`pyproject.toml` and inherit framework-default policies. Policies can
be explicitly adopted or skipped:

```toml
[tool.julee]
policies = ["postgresql-patterns"]
skip_policies = ["temporal-pipelines"]  # We don't use Temporal
```


## Documentation Philosophy (ADR 006)

Docstrings ARE the documentation. Hand-written prose for implemented
code is redundant. The framework's entity docstrings define the
concepts; Sphinx autodoc with entity-specific templates renders them.

Framework bounded contexts double as documentation viewpoints:

| Framework BC | Viewpoint | Projects |
|-------------|-----------|---------|
| `core` | Technical Framework | Entities, use cases, protocols |
| `hcd` | Human-Centred Design | Personas, journeys, stories |
| `c4` | Architecture | Systems, containers, components |

The `docs/design/` directory exists only for unimplemented features.
Once implemented, the design doc is deleted and the docstrings become
canonical.


## C4 Mapping

The clean architecture maps naturally to C4 diagrams:

```
Clean Architecture          C4 Model
──────────────────────────────────────────
Solution repository     →   Software System
apps/api/               →   Container (API)
apps/worker/            →   Container (Worker)
src/{bounded-context}/  →   Container (per domain)
entities/ classes       →   Entity Components
use_cases/ classes      →   Use Case Components
repositories/ protocols →   Protocol Components
services/ protocols     →   Protocol Components
```

Import analysis yields C4 relationships:

| Import Pattern | C4 Relationship |
|---------------|----------------|
| UseCase imports Repository | "reads from / writes to" |
| UseCase imports Service | "uses" |
| Pipeline imports UseCase | "executes" |
| API route imports UseCase | "exposes" |

A proposal exists (not yet implemented) to infer C4 diagrams directly
from code structure, AST introspection, and import analysis, avoiding
manual duplication between code and architecture documentation.


## External Dependencies

Julee solutions typically depend on:

| System | Role | Abstracted By |
|--------|------|--------------|
| Temporal | Workflow orchestration, durability, audit trails | Pipeline proxies, `ExecutionService`, `ClockService` |
| S3-compatible storage (MinIO) | Document and artefact persistence | Repository protocols |
| AI services (Anthropic, etc.) | Knowledge extraction, transformation | Service protocols |
| PostgreSQL | Temporal's persistence backend | Indirect (Temporal manages this) |

All external systems are hidden behind protocols. Use cases never
interact with external systems directly. Swapping Anthropic for OpenAI,
or MinIO for local filesystem, requires only a new infrastructure
implementation -- no changes to business logic.


## Summary

The architecture can be stated in seven rules:

1. **Bounded contexts at the top level** -- the codebase screams its
   business domain
2. **Dependencies point inward** -- entities know nothing; apps know
   everything
3. **Protocols in domain, implementations in infrastructure** --
   dependency inversion everywhere
4. **Use cases are the business logic boundary** -- one execute method,
   Request in, Response out
5. **Pipelines wrap use cases for durability** -- Temporal is
   infrastructure, not business logic
6. **Doctrine is executable** -- pytest tests enforce the architecture,
   not prose
7. **Code is the documentation** -- docstrings are canonical; everything
   else derives from them
