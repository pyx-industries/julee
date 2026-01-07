# ADR 010: Apps Layer and Reserved Words Architecture

## Status

Draft

## Date

2026-01-07

## Context

A Julee solution contains bounded contexts (BCs) organized as top-level directories. However, not every top-level directory is a bounded context. Some directories have special architectural meaning:

- `apps/` contains deployable applications that consume bounded contexts
- `deployments/` contains deployment configurations
- `docs/` contains documentation

Without clear rules:
- Doctrine might incorrectly identify `apps/` as a bounded context
- Developers might place application code inside bounded contexts
- The dependency direction between apps and BCs becomes unclear
- Nested solutions (like `contrib/`) might be mishandled

The framework needs explicit rules for:
1. Which directories are bounded contexts vs reserved words
2. How applications relate to bounded contexts
3. How nested solutions work

## Decision

### Reserved Words

Certain top-level directory names are **reserved words** - they have special architectural meaning and are NOT bounded contexts.

| Reserved Word | Constant | Purpose |
|---------------|----------|---------|
| `apps` | `APPS_ROOT` | Application layer entry points |
| `deployments` | `DEPLOYMENTS_ROOT` | Deployment configurations |
| `deployment` | `LAYER_DEPLOYMENT` | Legacy singular form |
| `docs` | `DOCS_ROOT` | Documentation (required for every solution) |

Every top-level directory is treated as a bounded context (or nested solution) **except** reserved words.

### Bounded Context Discovery

Doctrine discovers bounded contexts by:

1. Scanning top-level directories under the solution root
2. Excluding reserved words
3. Checking for Clean Architecture markers (`entities/` or `use_cases/`)
4. Verifying the directory is a Python package (`__init__.py`)

```python
# Simplified discovery logic
for directory in solution_root.iterdir():
    if directory.name in RESERVED_WORDS:
        continue  # Skip reserved words
    if not (directory / "__init__.py").exists():
        continue  # Must be a Python package
    if has_entities_or_use_cases(directory):
        yield BoundedContext(slug=directory.name)
```

### Apps Layer

The `apps/` directory contains deployable applications. Each subdirectory is an application:

```
apps/
├── __init__.py
├── api/              # e.g. FastAPI REST API
│   ├── __init__.py
│   ├── app.py
│   └── routers/
├── admin/            # e.g. CLI admin tool
│   ├── __init__.py
│   ├── cli.py
│   └── commands/
├── worker/           # e.g. background worker
│   ├── __init__.py
│   └── pipelines.py
└── mcp/              # e.g. MCP server
    ├── __init__.py
    └── context.py
```

### Dependency Direction

Applications depend on bounded contexts. Bounded contexts MUST NOT depend on applications.

```
┌─────────────────────────────────────────────────────┐
│                    apps/                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │   api   │  │  admin  │  │  worker │  ...       │
│  └────┬────┘  └────┬────┘  └────┬────┘            │
│       │            │            │                  │
│       └────────────┼────────────┘                  │
│                    │ depends on                    │
│                    ▼                               │
├─────────────────────────────────────────────────────┤
│              Bounded Contexts                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │   hcd   │  │   ceap  │  │  core   │  ...       │
│  └─────────┘  └─────────┘  └─────────┘            │
└─────────────────────────────────────────────────────┘
```

This means:
- Apps import from BCs: `from julee.hcd.use_cases import CreateStoryUseCase`
- BCs never import from apps
- BCs have no knowledge of which apps consume them

### Apps as Composition Roots

Applications serve as **composition roots** - they wire together:
- Use cases from bounded contexts
- Repository implementations from infrastructure
- Service implementations from infrastructure
- Configuration and environment handling

```python
# apps/api/dependencies.py
from julee.hcd.use_cases import CreateStoryUseCase
from julee.hcd.infrastructure.repositories.postgres import PostgresStoryRepository

def get_create_story_use_case() -> CreateStoryUseCase:
    repo = PostgresStoryRepository(get_db_session())
    return CreateStoryUseCase(repo)
```

### Nested Solutions

A **nested solution** is a directory that contains its own bounded contexts and reserved words. The julee framework includes `contrib/` as a nested solution providing reusable functionality for implementers.

```
solution_root/
├── hcd/                  # BC
├── ceap/                 # BC
├── contrib/              # Nested solution
│   ├── polling/          # BC within nested solution
│   ├── untp/             # BC within nested solution
│   └── apps/             # Reserved word within nested solution
├── apps/                 # Reserved word
└── docs/                 # Reserved word
```

Nested solutions follow the same rules recursively:
- Their subdirectories are BCs except reserved words
- They may have their own `apps/`, `docs/`, etc.

Other julee solutions (not the framework itself) may also have nested solutions if that makes sense for their architecture.

### What Apps Contain

Applications typically contain:

| Component | Purpose | Example |
|-----------|---------|---------|
| Entry point | Application initialization | `app.py`, `cli.py`, `__main__.py` |
| Dependencies | Composition root / DI wiring | `dependencies.py` |
| Routers | HTTP route handlers (FastAPI) | `routers/*.py` |
| Commands | CLI command handlers (Typer) | `commands/*.py` |
| Context | MCP server context | `context.py` |
| Pipelines | Temporal workflow definitions | `pipelines.py` |

### What Apps Do NOT Contain

Applications MUST NOT contain:
- Entities (belong in BCs)
- Use cases (belong in BCs)
- Repository protocols (belong in BCs)
- Service protocols (belong in BCs)
- Business logic (belongs in use cases)

Applications are thin layers that:
1. Accept external input (HTTP, CLI, messages)
2. Translate to use case requests
3. Execute use cases
4. Translate responses to external output

## Consequences

### Positive

1. **Clear separation** - Apps and BCs have distinct responsibilities
2. **Dependency clarity** - One-way dependency from apps to BCs
3. **Doctrine enforceable** - Reserved words prevent false BC detection
4. **Reusable BCs** - Same BC can be used by multiple apps
5. **Testable in isolation** - BCs can be tested without app infrastructure
6. **Nested solution support** - Complex solutions can organize sub-solutions

### Negative

1. **Directory proliferation** - More top-level directories to manage
2. **Import path length** - `from julee.contrib.polling.use_cases...`

### Neutral

1. **Convention over configuration** - Directory names have meaning

## Implementation

### Doctrine Constants

```python
# julee/core/doctrine_constants.py
APPS_ROOT: Final[str] = "apps"
DEPLOYMENTS_ROOT: Final[str] = "deployments"
DOCS_ROOT: Final[str] = "docs"

RESERVED_WORDS: Final[frozenset[str]] = frozenset({
    APPS_ROOT,
    DEPLOYMENTS_ROOT,
    DOCS_ROOT,
})
```

### Doctrine Tests

- `julee/core/doctrine/test_bounded_context.py` - BC discovery excludes reserved words
- Reserved words are derived from doctrine constants, not hardcoded

### Application Discovery

Applications within `apps/` can be discovered for documentation and tooling:

```python
class FilesystemApplicationRepository:
    """Discovers applications in the apps/ directory."""

    async def list_all(self) -> list[Application]:
        apps_dir = self.solution_root / APPS_ROOT
        for app_dir in apps_dir.iterdir():
            if app_dir.is_dir() and (app_dir / "__init__.py").exists():
                yield Application(slug=app_dir.name, path=app_dir)
```

## Alternatives Considered

### 1. Apps as a Bounded Context

Treat `apps/` as a special bounded context.

**Rejected**: Apps don't follow BC structure (no entities, no use cases). They're a different architectural layer.

### 2. Apps Inside Bounded Contexts

Each BC has its own `apps/` subdirectory.

**Rejected**: Creates tight coupling. An app often needs multiple BCs, so it belongs outside them.

### 3. No Reserved Words

Let doctrine figure out what's a BC based solely on structure.

**Rejected**: Directories like `apps/` might accidentally contain `entities/` for their own models, causing false detection.

### 4. Explicit Configuration

Require solutions to list their BCs in configuration.

**Rejected**: Violates convention over configuration. Directory structure should be self-documenting.

## References

- [ADR 001: Contrib Module Layout](./001-contrib-layout.md)
- [ADR 002: Doctrine Test Architecture](./002-doctrine-test-architecture.md)
- Issue #66: ADR needed: Apps Layer and Reserved Words Architecture
