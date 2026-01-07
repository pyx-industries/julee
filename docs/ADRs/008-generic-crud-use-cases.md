# ADR 008: Generic CRUD Use Case Generators

## Status

Draft

## Date

2026-01-07

## Context

Clean Architecture provides clarity through single responsibility and well-defined interfaces. However, it creates verbosity - each entity typically needs five boilerplate use cases:

- `Get{Entity}UseCase` - retrieve by identifier
- `List{Entities}UseCase` - list all (with optional filtering)
- `Create{Entity}UseCase` - create new entity
- `Update{Entity}UseCase` - modify existing entity
- `Delete{Entity}UseCase` - remove entity

Each use case requires matching Request and Response classes, leading to 15 classes per entity for basic CRUD operations. This boilerplate:

1. **Obscures business logic** - the interesting use cases get lost among identical CRUD implementations
2. **Creates maintenance burden** - changes to patterns require updating many files
3. **Violates DRY** - the same patterns are repeated with only entity names changed
4. **Discourages doctrine compliance** - developers may skip proper structure to avoid boilerplate

The challenge is reducing boilerplate while:
- Maintaining doctrine compliance (use cases have execute(), matching Request/Response)
- Preserving type safety and IDE support
- Allowing customization when needed
- Keeping generated code discoverable

## Decision

The framework SHALL provide generic CRUD base classes and a `generate()` factory function that creates doctrine-compliant use cases with minimal boilerplate.

### Base Classes for Inheritance

For cases requiring customization, generic base classes enable subclassing:

```python
from julee.core.use_cases import generic_crud
from julee.hcd.entities.story import Story
from julee.hcd.repositories.story import StoryRepository

class GetStoryUseCase(generic_crud.GetUseCase[Story, StoryRepository]):
    """Get a story by slug."""

class ListStoriesUseCase(generic_crud.ListUseCase[Story, StoryRepository]):
    """List all stories."""
```

Base classes are parameterized by entity type `E` and repository type `R`, providing:
- Type-safe repository injection
- Standard execute() method implementation
- Auto-derived response field names (e.g., `response.story`, `response.stories`)

### The generate() Factory

For standard CRUD without customization, a single call generates all classes:

```python
from julee.core.use_cases import generic_crud

generic_crud.generate(
    Story,
    StoryRepository,
    filters=["app_slug", "persona"],
)

# Generates and injects into module namespace:
# - GetStoryRequest, GetStoryResponse, GetStoryUseCase
# - ListStoriesRequest, ListStoriesResponse, ListStoriesUseCase
# - CreateStoryRequest, CreateStoryResponse, CreateStoryUseCase
# - UpdateStoryRequest, UpdateStoryResponse, UpdateStoryUseCase
# - DeleteStoryRequest, DeleteStoryResponse, DeleteStoryUseCase
```

The generator:
1. Uses repository protocol to infer Request/Response properties
2. Applies pluralization rules (`Story` → `Stories`, `Journey` → `Journeys`)
3. Injects classes into the calling module's namespace
4. Supports optional `filters` parameter for List filtering

### Auto-Derived Field Names

Response classes automatically derive field names from entity types:

```python
# GetResponse[SoftwareSystem] serializes as:
{"software_system": {...}}

# ListResponse[Story] serializes as:
{"stories": [...]}
```

This is achieved through:
- `_to_snake_case()` - converts `SoftwareSystem` to `software_system`
- `_pluralize()` - converts `story` to `stories` (handles consonant+y, -s, -x, -ch)
- Custom `__getattr__` for attribute access (`response.stories`)
- Custom `model_serializer` for JSON output

### Filterable Lists

The `FilterableListUseCase` base class delegates filtering to the repository:

```python
class ListStoriesUseCase(generic_crud.FilterableListUseCase[Story, StoryRepository]):
    """List stories with optional filtering."""

# Repository protocol declares available filters:
class StoryRepository(Protocol):
    async def list_filtered(
        self,
        app_slug: str | None = None,
        persona: str | None = None,
    ) -> list[Story]: ...
```

The `make_list_request()` helper introspects repository signatures to generate matching request classes:

```python
ListStoriesRequest = generic_crud.make_list_request(
    "ListStoriesRequest",
    StoryRepository,
)
# Generates request with app_slug and persona filter fields
```

### Handler Integration

Create and Update use cases support optional handlers for workflow orchestration (see ADR 003):

```python
class CreateUseCase(Generic[E, R]):
    def __init__(self, repo: R, post_create_handler: Any | None = None) -> None:
        self.repo = repo
        self.post_create_handler = post_create_handler

    async def execute(self, request: CreateRequest) -> CreateResponse[E]:
        entity = self.entity_cls.from_create_data(**request.model_dump())
        await self.repo.save(entity)

        if self.post_create_handler is not None:
            await self.post_create_handler.handle(entity)

        return self.response_cls(entity=entity)
```

### Customization Points

Generated classes can be customized by:

1. **Subclassing base classes** - for custom execute() logic
2. **Entity methods** - `from_create_data()`, `apply_update()` for creation/update logic
3. **Replacing generated classes** - define your own after generate() call
4. **Selective generation** - `generate(..., delete=False, update=False)`

## Consequences

### Positive

1. **Reduced boilerplate** - one line generates 15 doctrine-compliant classes
2. **Consistent patterns** - all CRUD operations follow identical structure
3. **Doctrine compliance** - generated classes satisfy all doctrine requirements
4. **Type safety preserved** - generics maintain type checking
5. **Customizable** - base classes allow override when needed
6. **Repository-driven filters** - list filters derived from repository protocol

### Negative

1. **IDE limitations** - generated classes may not appear in autocomplete until runtime
2. **Debugging complexity** - stack traces include generic base classes
3. **Magic behavior** - namespace injection is implicit
4. **Learning curve** - developers must understand the generation pattern

### Neutral

1. **Not required** - bounded contexts can always write explicit CRUD classes
2. **Complements hand-written** - generated and custom use cases coexist

## Implementation

### Core Module

`julee/core/use_cases/generic_crud.py` provides:

- Base classes: `GetUseCase`, `ListUseCase`, `FilterableListUseCase`, `PaginatedListUseCase`, `CreateUseCase`, `UpdateUseCase`, `DeleteUseCase`
- Request bases: `GetRequest`, `ListRequest`, `PaginatedListRequest`, `CreateRequest`, `UpdateRequest`, `DeleteRequest`
- Response bases: `GetResponse`, `ListResponse`, `PaginatedListResponse`, `CreateResponse`, `UpdateResponse`, `DeleteResponse`
- Helpers: `generate()`, `make_list_request()`, `extract_filter_params()`

### Usage Pattern

Bounded contexts create a `use_cases/crud.py` module:

```python
"""CRUD use cases for HCD entities."""

from julee.core.use_cases import generic_crud
from julee.hcd.entities import Story, Epic, Persona
from julee.hcd.repositories import StoryRepository, EpicRepository, PersonaRepository

generic_crud.generate(Story, StoryRepository, filters=["app_slug", "persona"])
generic_crud.generate(Epic, EpicRepository, filters=["app_slug"])
generic_crud.generate(Persona, PersonaRepository)
```

## Alternatives Considered

### 1. Code Generation Scripts

Generate Python files at build time.

**Rejected**: Creates files that drift from source of truth, complicates version control, requires build step.

### 2. Metaclass-Based Generation

Use metaclasses to generate methods on entity classes.

**Rejected**: Mixes entity and use case concerns, violates Clean Architecture layer separation.

### 3. Decorator-Based Generation

```python
@crud_entity(StoryRepository)
class Story(BaseModel):
    ...
```

**Rejected**: Couples entity definition to use case generation, makes dependencies unclear.

### 4. No Generation - Explicit Only

Require all CRUD classes to be hand-written.

**Rejected**: Excessive boilerplate discourages doctrine compliance and obscures business logic.

## References

- [ADR 003: Workflow Orchestration via Handler Services](./003-workflow-orchestration-handlers.md)
- [ADR 002: Doctrine Test Architecture](./002-doctrine-test-architecture.md)
- Issue #64: ADR needed: Generic CRUD Use Case Generators
