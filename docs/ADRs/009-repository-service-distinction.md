# ADR 009: Repository vs Service Protocol Distinction

## Status

Draft

## Date

2026-01-07

## Context

Clean Architecture defines two primary abstraction mechanisms for infrastructure concerns:

- **Repositories** - abstract data persistence
- **Services** - abstract external capabilities

However, the boundary between these concepts is often unclear in practice. Questions arise:

- If a service persists data, is it a repository?
- If a repository transforms data before returning it, is it a service?
- What about adapters that call external APIs?
- How do we decide where to put a new protocol?

This ambiguity leads to inconsistent architecture decisions across bounded contexts. Different developers make different choices for similar situations, making the codebase harder to navigate and understand.

The framework needs a clear, enforceable distinction that:
- Is simple enough to apply without debate
- Covers all practical cases
- Can be validated by doctrine tests

## Decision

The distinction between repositories and services SHALL be based on **entity cardinality**:

> **A repository interface is semantically bound to ONE entity type.**
> **A service interface is semantically bound to TWO OR MORE entity types.**

This is the definitional difference. Everything else follows from it.

### Repository: One Entity

A repository protocol is bound to a single entity type. Its methods accept and return instances of that entity (or primitives like identifiers).

```python
class StoryRepository(Protocol):
    """Repository for Story persistence."""

    async def get(self, slug: str) -> Story | None: ...
    async def save(self, story: Story) -> None: ...
    async def delete(self, slug: str) -> bool: ...
    async def list_all(self) -> list[Story]: ...
    async def list_filtered(self, app_slug: str | None = None) -> list[Story]: ...
```

The repository knows only about `Story`. It doesn't transform stories into other entity types.

### Service: Multiple Entities (Transformation)

A service protocol is bound to two or more entity types. It typically performs **transformation** - accepting one entity type and producing another.

```python
class KnowledgeService(Protocol):
    """Service for extracting knowledge from documents."""

    async def extract(self, document: Document) -> Knowledge: ...
    async def query(self, knowledge: Knowledge, question: str) -> Answer: ...
```

This service transforms `Document` → `Knowledge` and `Knowledge` → `Answer`. It's bound to three entity types.

```python
class AssemblyService(Protocol):
    """Service for assembling documents from components."""

    async def assemble(
        self,
        spec: AssemblySpecification,
        extractions: list[Extraction],
    ) -> Assembly: ...
```

This service combines `AssemblySpecification` + `Extraction` → `Assembly`. Multiple input types, different output type.

### Common Properties

Both repositories and services share these characteristics:

| Property | Repository | Service |
|----------|------------|---------|
| Defined as | Protocol (interface) | Protocol (interface) |
| Location | `{bc}/repositories/` | `{bc}/services/` |
| Implementation | `{bc}/infrastructure/` | `{bc}/infrastructure/` |
| Injected into | Use cases | Use cases |
| Deals in | Domain objects and primitives | Domain objects and primitives |

### What About...?

**External API adapters?**
- If they return a single entity type → Repository (e.g., `WeatherRepository` returning `Weather`)
- If they transform between types → Service (e.g., `GeocodingService` taking `Address` returning `Coordinates`)

**Caching layers?**
- Caching is an implementation detail. The protocol is still Repository or Service based on entity cardinality.

**AI/ML integrations?**
- Same rule. `EmbeddingService` taking `Text` returning `Embedding` is a Service (two types).

**Query services?**
- If queries return the same entity type → Repository method (e.g., `list_filtered`)
- If queries combine/transform multiple types → Service

### Naming Conventions

Protocols MUST use the appropriate suffix:

- Repository protocols: `{Entity}Repository` (e.g., `StoryRepository`)
- Service protocols: `{Capability}Service` (e.g., `KnowledgeService`, `AssemblyService`)

### Directory Structure

```
{bounded_context}/
├── repositories/           # Repository protocols (one entity each)
│   ├── __init__.py
│   ├── story.py           # StoryRepository
│   └── epic.py            # EpicRepository
├── services/              # Service protocols (multiple entities)
│   ├── __init__.py
│   └── knowledge.py       # KnowledgeService
└── infrastructure/        # Implementations of both
    ├── repositories/
    │   ├── memory/
    │   └── postgres/
    └── services/
        └── anthropic/
```

### Doctrine Enforcement

Doctrine tests validate:

1. **Naming**: Repository protocols end with `Repository`, services end with `Service`
2. **Inheritance**: Both must inherit from `Protocol`
3. **Documentation**: Both must have docstrings
4. **Location**: Protocols in domain layer, implementations in infrastructure

## Consequences

### Positive

1. **Clear decision rule** - Entity cardinality is unambiguous and easy to apply
2. **Consistent architecture** - All bounded contexts follow the same pattern
3. **Doctrine enforceable** - Naming conventions can be automatically validated
4. **Guides refactoring** - When a repository starts handling multiple entities, it should become a service

### Negative

1. **May require refactoring** - Existing code mixing concerns needs restructuring
2. **Strict interpretation** - Edge cases require thought about which entity types are involved

### Neutral

1. **Implementation flexibility** - The rule is about protocols, not implementations. A service implementation may internally use repositories.

## Examples

### Repository Examples

```python
# Single entity: Document
class DocumentRepository(Protocol):
    async def get(self, doc_id: str) -> Document | None: ...
    async def save(self, doc: Document) -> None: ...

# Single entity: Persona
class PersonaRepository(Protocol):
    async def get(self, slug: str) -> Persona | None: ...
    async def list_by_journey(self, journey_slug: str) -> list[Persona]: ...
```

### Service Examples

```python
# Multiple entities: Document → Extraction
class ExtractionService(Protocol):
    async def extract(self, document: Document) -> Extraction: ...

# Multiple entities: various inputs → SuggestionContext
class SuggestionContextService(Protocol):
    async def build_context(
        self,
        story: Story,
        personas: list[Persona],
        related_stories: list[Story],
    ) -> SuggestionContext: ...

# Multiple entities: ClassInfo, MethodInfo → EvaluationResult
class SemanticEvaluationService(Protocol):
    async def evaluate(
        self,
        class_info: ClassInfo,
        methods: list[MethodInfo],
    ) -> EvaluationResult: ...
```

## Implementation

### Doctrine Tests

- `julee/core/doctrine/test_repository_protocol.py` - Repository naming, inheritance, documentation
- `julee/core/doctrine/test_service_protocol.py` - Service naming, inheritance, documentation

### Constants

```python
# julee/core/doctrine_constants.py
REPOSITORY_SUFFIX: Final[str] = "Repository"
SERVICE_SUFFIX: Final[str] = "Service"
```

## Alternatives Considered

### 1. Persistence vs Capability

Repositories for persistence, services for everything else.

**Rejected**: Too vague. What about external data sources? Caching? The line between "persistence" and "capability" is unclear.

### 2. Internal vs External

Repositories for internal data, services for external integrations.

**Rejected**: Doesn't hold. External APIs that return a single entity type (weather, exchange rates) fit the repository pattern better.

### 3. Synchronous vs Asynchronous

Repositories for sync access, services for async operations.

**Rejected**: Implementation detail, not architectural distinction. Both can be async.

### 4. No Formal Distinction

Let developers decide case-by-case.

**Rejected**: Leads to inconsistency. Different BCs would make different choices for identical situations.

## References

- [ADR 002: Doctrine Test Architecture](./002-doctrine-test-architecture.md)
- Clean Architecture (Robert C. Martin)
- Issue #65: ADR needed: Repository vs Service Protocol Distinction
