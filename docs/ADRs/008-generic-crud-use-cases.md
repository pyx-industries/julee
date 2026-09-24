# ADR 008: Generic CRUD Use Case Generators

## Status

Accepted

## Date

2026-01-07

## Revision

2026-03-24

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

The framework SHALL provide generic CRUD base classes and a build-time code generator that produces plain Python files from entity and repository definitions.

Generated files are placed in a `.generated/` directory within each bounded context, gitignored, and regenerated as part of `make install`. Because the generator is deterministic (same entity + repository definitions → same output), the generated files are fully derivable from tracked source — the same model as compiled artifacts.

### Base Classes for Inheritance

Generic base classes parameterized by entity type `E` and repository type `R` provide the implementations that generated classes inherit from:

```python
from julee.core.usecases import generic_crud
from julee_hcd.domain.models.story import Story
from julee_hcd.domain.repositories.story import StoryRepository

class GetStoryUseCase(generic_crud.GetUseCase[Story, StoryRepository]):
    """Get a story by slug."""

class ListStoriesUseCase(generic_crud.ListUseCase[Story, StoryRepository]):
    """List all stories."""
```

For cases not requiring customization, the code generator emits subclasses like these automatically.

### The Code Generator

`julee/core/usecases/generate_crud.py` is a CLI script that accepts an entity and its repository, the field that identifies it, and the fields each request carries, and writes a `crud_{entity_snake}.py` file into the target directory:

```bash
uv run python -m julee.core.usecases.generate_crud \
    --entity Story --entity-module julee_hcd.domain.models.story \
    --repo StoryRepository --repo-module julee_hcd.domain.repositories.story \
    --id-field slug --out src/julee_hcd/usecases \
    --create-fields 'slug:str title:str app_slug:str persona:str=""' \
    --update-fields 'title:str app_slug:str persona:str'
```

The generator:
1. Inspects the repository Protocol to derive filter parameter names and types
2. Applies naming rules (`Story` → `Stories`, `SoftwareSystem` → `software_systems`)
3. Writes a single `.py` file containing all 15 classes (5 operations × Request + Response + UseCase)
4. Pipes output through `ruff format` for consistent style

The generated file is ordinary Python — fully visible to IDEs, debuggable with standard tools, and readable by developers who want to understand what the pattern produces.

### Auto-Derived Field Names

Response classes automatically derive field names from entity types:

```python
# GetResponse[SoftwareSystem] serializes as:
{"software_system": {...}}

# ListResponse[Story] serializes as:
{"stories": [...]}
```

Naming helpers in the generator:
- `_to_snake_case()` - converts `SoftwareSystem` to `software_system`
- `_pluralize()` - converts `story` to `stories` (handles consonant+y, -s, -x, -ch)

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

The generator introspects the repository Protocol signature to emit matching request fields.

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

1. **Subclassing base classes** - write a hand-rolled use case that extends the generic base
2. **Entity methods** - `from_create_data()`, `apply_update()` for creation/update logic
3. **Selective generation** - pass `--no-delete`, `--no-update` flags to the generator
4. **Override after generation** - import the generated class and subclass it; the generator will not overwrite hand-rolled files

## Consequences

### Positive

1. **Full IDE support** - generated files are plain Python; autocomplete, go-to-definition, and refactoring all work
2. **Debuggable** - stack traces reference real file lines in `.generated/`, not generic base class internals
3. **Clean diffs** - generated files are gitignored and never appear in PRs
4. **No magic** - the generation step is explicit and inspectable; running it produces readable output
5. **Doctrine compliance** - generated classes satisfy all doctrine requirements via base class inheritance
6. **Consistent patterns** - all CRUD operations follow identical structure

### Negative

1. **Build step required** - `make install` must be run before the generated files exist
2. **Generator must be kept current** - changes to base class interfaces require regenerating affected files

### Neutral

1. **Not required** - bounded contexts can always write explicit CRUD classes
2. **Complements hand-written** - generated and custom use cases coexist

## Implementation

### Core Module

`julee/core/usecases/generic_crud.py` provides four base classes: `GetUseCase`, `ListUseCase`, `CreateUseCase` and `UpdateUseCase`.

There is no `DeleteUseCase`, so "CRUD" stops at three letters and every kit with removable entities hand-writes the fourth. See #198, which also has to settle what deleting something absent means.

Requests and responses are **not** in the kernel. Each is generated per entity — `GetStoryRequest`, `CreateStoryResponse` — because their fields are the entity's, and a shared `CreateRequest` could only have been untyped.

`julee/core/usecases/generate_crud.py` provides the CLI generator.

### Directory Convention

```
src/
  julee_hcd/
    domain/
      models/
        story.py          # tracked
      repositories/
        story.py          # tracked
    usecases/
      crud_story.py       # generated, and tracked — see below
```

### Whether generated output is committed

A **solution** may gitignore it and regenerate on install, since the source is always at hand.

A **kit** commits it. A kit ships as a wheel, and what is not in the repository is not in the distribution, so generated code that exists only after a build step is code the kit does not actually ship. The five kits commit theirs.

### Regenerating

The generator takes one entity at a time, because the fields each entity's requests carry are the entity's own and there is nothing to infer them from. A kit therefore keeps a script that names them all:

```sh
# c4/generate-crud.sh
out=src/julee_c4/usecases
gen() {
  uv run python -m julee.core.usecases.generate_crud \
    --entity "$1" --entity-module "julee_c4.domain.models.$2" \
    --repo "$1Repository" --repo-module "julee_c4.domain.repositories.$2" \
    --id-field slug --out "$out" \
    --create-fields "$3" --update-fields "$4"
}

gen Component component \
  'slug:str name:str container_slug:str description:str=""' \
  'name:str container_slug:str description:str'
```

`--no-get`, `--no-list`, `--no-create` and `--no-update` each skip one.

## Alternatives Considered

### 1. Runtime Namespace Injection (previously the chosen approach)

Generate classes at module load time and inject them into the calling module's namespace via `generate()`.

**Rejected**: IDEs cannot discover injected names until the module is imported at runtime, breaking autocomplete and go-to-definition. Stack traces reference generic base classes rather than meaningful locations. The implicit namespace mutation is opaque to readers of the calling module.

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

### 5. Generated Files Committed to Version Control

Store generated files in a `.generated/` directory tracked by git, using `.gitattributes` to mark them as generated so GitHub collapses them in PR diffs.

**Rejected**: Generated files still appear in PRs (collapsed, but present). Developers can accidentally edit them and the edit persists until the next regeneration. Keeping them out of VCS entirely is cleaner — the files are derivable from tracked source, so committing them adds noise without benefit.

## References

- [ADR 003: Workflow Orchestration via Handler Services](./003-workflow-orchestration-handlers.md)
- [ADR 002: Doctrine Test Architecture](./002-doctrine-test-architecture.md)
- Issue #64: ADR needed: Generic CRUD Use Case Generators
