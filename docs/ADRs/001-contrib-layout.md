# ADR 001: Contrib Module Layout

## Status

Draft

## Date

2025-12-09

## Context

The Julee framework includes "contrib" modules - ready-made, batteries-included components that solutions can import and use. Currently identified contrib modules are:

- **CEAP**: The Capture-Extract-Assemble-Publish workflow pattern
- **Ontology Mapper**: Ontology mapping and transformation service

These modules are currently either entangled with the framework core (CEAP) or living in separate repositories (ontology-mapper). This creates several problems:

1. **Unclear boundaries**: CEAP code is mixed with framework infrastructure code
2. **Inconsistent structure**: No standard for how contrib modules should be organised
3. **Reusability friction**: Difficult for solutions to selectively import and customise contrib modules
4. **Testing confusion**: Unclear where contrib module tests belong

We need a consistent layout for `julee.contrib.*` modules that:
- Makes each module a self-contained Julee solution
- Allows modules to be run standalone OR imported into other solutions
- Follows the same patterns used by external Julee solutions
- Keeps tests co-located with the code they test

## Decision

Each `julee.contrib.*` module SHALL be structured as a self-contained Julee solution, following the same architecture pattern used by external solutions.

In solution architecture parlance, **contrib modules are accelerators** - reusable bounded contexts that can be imported and composed into larger solutions.

### Directory Structure

```
src/julee/contrib/
├── __init__.py                           # Contrib namespace
│
├── ceap/                                 # Contrib module: CEAP workflow
│   ├── __init__.py                       # Public API exports
│   │
│   ├── domain/                           # Domain layer
│   │   ├── __init__.py
│   │   ├── models/                       # Entities (if module-specific)
│   │   │   └── __init__.py
│   │   ├── repositories/                 # Repository PROTOCOLS
│   │   │   └── __init__.py
│   │   └── services/                     # Service PROTOCOLS
│   │       └── __init__.py
│   │
│   ├── use_cases/                        # Application business rules
│   │   ├── __init__.py
│   │   ├── extract_assemble_data.py
│   │   └── validate_document.py
│   │
│   ├── infrastructure/                   # Implementations
│   │   ├── __init__.py
│   │   ├── repositories/
│   │   │   ├── minio/                    # Layer 1: Production
│   │   │   ├── memory/                   # Layer 1: Testing
│   │   │   └── temporal/                 # Layers 2 & 3
│   │   └── services/
│   │       └── temporal/                 # Layers 2 & 3
│   │
│   ├── apps/                             # Application entry points
│   │   ├── __init__.py
│   │   ├── api/                          # FastAPI routes
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── cli/                          # CLI commands
│   │   │   ├── __init__.py
│   │   │   └── commands.py
│   │   └── worker/                       # Worker components
│   │       ├── __init__.py
│   │       └── pipelines.py              # Use cases treated for durability
│   │
│   ├── deploy/                           # Deployment artifacts (optional)
│   │   ├── docker/
│   │   │   ├── docker-compose.yml        # Single file with profiles
│   │   │   ├── Dockerfile.api
│   │   │   └── Dockerfile.worker
│   │   └── ansible/                      # Infrastructure as Code (optional)
│   │       ├── inventory/
│   │       ├── playbooks/
│   │       └── roles/
│   │
│   └── tests/                            # Co-located tests
│       ├── __init__.py
│       ├── conftest.py                   # Module-specific fixtures
│       ├── unit/
│       │   ├── __init__.py
│       │   ├── test_extract_assemble.py
│       │   └── test_validate_document.py
│       └── integration/
│           └── __init__.py
│
└── ontology_mapper/                      # Contrib module: Ontology Mapper
    ├── __init__.py
    ├── domain/
    │   └── ...
    ├── use_cases/
    │   └── ...
    ├── infrastructure/
    │   └── ...
    ├── apps/
    │   └── ...
    ├── deploy/                           # (optional)
    │   └── ...
    └── tests/
        └── ...
```

### Key Principles

#### 1. Contrib Modules are Accelerators

In Julee solution architecture, an **accelerator** is a collection of pipelines that work together to make an area of business go faster. Contrib modules are pre-built accelerators that ship with the framework.

Each contrib module has the same structure as an external Julee solution:
- `domain/`: Models, repository protocols, service protocols
- `use_cases/`: Business logic
- `infrastructure/`: Repository and service implementations
- `apps/`: Entry points (API routes, CLI commands, worker pipelines)
- `deploy/`: Deployment artifacts (optional, for standalone deployment)
- `tests/`: Co-located test suite

This means a contrib module can theoretically be extracted to its own repository and deployed independently.

#### 2. Tests Co-located Within Modules

Tests live inside each contrib module in a `tests/` subdirectory. This:
- Ships tests with the module (useful for downstream verification)
- Makes ownership clear
- Follows existing Julee conventions (`julee/domain/models/*/tests/`)
- Works with pytest's test discovery (`testpaths = ["src/julee"]`)

#### 3. Modules Import from Framework Core

Contrib modules import shared infrastructure from the Julee framework core - utilities, base classes, and decorators that are genuinely framework-level concerns.

Contrib modules do NOT duplicate framework code. They extend and compose it.

Any shared utilities needed by multiple contrib modules belong in the framework core (e.g., `julee.util`), not in a shadow framework within contrib.

#### 4. Public API via `__init__.py`

Each module's `__init__.py` exports the public API:

```python
# julee/contrib/ceap/__init__.py
from .use_cases import ExtractAssembleDataUseCase, ValidateDocumentUseCase
from .apps.worker.pipelines import ExtractAssemblePipeline, ValidateDocumentPipeline

__all__ = [
    "ExtractAssembleDataUseCase",
    "ValidateDocumentUseCase",
    "ExtractAssemblePipeline",
    "ValidateDocumentPipeline",
]
```

Solutions import from the module root:

```python
from julee.contrib.ceap import ExtractAssembleDataUseCase
from julee.contrib.ontology_mapper import MapOntologyUseCase
```

#### 5. Apps Provide Integration Points

The `apps/` directory provides ready-to-use integration points:

- **`apps/api/`**: FastAPI router that can be mounted in a solution's API
- **`apps/cli/`**: Typer commands that can be registered in a solution's CLI
- **`apps/worker/pipelines.py`**: Pipelines ready to register with a worker

Solutions wire these into their own apps:

```python
# Solution's apps/api/app.py
from fastapi import FastAPI
from julee.contrib.ceap.apps.api import router as ceap_router

app = FastAPI()
app.include_router(ceap_router, prefix="/ceap")
```

#### 6. Deploy Directory for Standalone Operation

The optional `deploy/` directory enables a contrib module to run as a standalone service:

- **`deploy/docker/`**: Docker Compose configuration with profiles
- **`deploy/ansible/`**: Infrastructure as Code for production deployment

**Docker Compose Profiles**:

```bash
# Run the contrib module standalone with infrastructure
docker compose --profile dev up

# Just infrastructure for local development
docker compose --profile infra up

# Test environment
docker compose --profile test up
```

When a contrib module is imported into a larger solution, the solution provides its own deployment configuration. The contrib module's `deploy/` directory is for standalone operation or reference.

### Optional Components

Not all contrib modules need all directories. The minimal structure is:

```
contrib_module/
├── __init__.py
├── use_cases/
└── tests/
```

Additional directories are added as needed:

| Directory | When to Include |
|-----------|-----------------|
| `domain/models/` | Module defines its own entities beyond framework core |
| `domain/repositories/` | Module defines new repository protocols |
| `domain/services/` | Module defines new service protocols |
| `infrastructure/` | Module provides implementations (not just protocols) |
| `apps/api/` | Module can expose REST endpoints |
| `apps/cli/` | Module provides CLI commands |
| `apps/worker/` | Module has pipelines |
| `deploy/docker/` | Module can run standalone |
| `deploy/ansible/` | Module has production IaC |

### Examples Location

Examples and sample applications live at the repository root, NOT inside contrib modules:

```
examples/
├── README.md
├── ceap_quickstart/
│   ├── README.md
│   ├── main.py
│   └── sample_data/
├── ontology_mapper_basic/
│   └── ...
└── full_solution/                # Complete solution example
    ├── pyproject.toml
    ├── src/
    │   └── my_solution/
    └── apps/
```

**Rationale**:
- Examples are not part of the installed package
- Can have their own dependencies
- Easier to copy as starting points
- Follows Django/FastAPI conventions

### Migration Path

Existing CEAP code moves from framework core to contrib:

| Current Location | New Location |
|-----------------|--------------|
| `julee/domain/use_cases/extract_assemble_data.py` | `julee/contrib/ceap/use_cases/` |
| `julee/domain/use_cases/validate_document.py` | `julee/contrib/ceap/use_cases/` |
| `julee/workflows/extract_assemble.py` | `julee/contrib/ceap/apps/worker/pipelines.py` |
| `julee/workflows/validate_document.py` | `julee/contrib/ceap/apps/worker/pipelines.py` |

Backwards-compatible re-exports from old locations during transition period.

## Consequences

### Positive

1. **Consistent structure**: All contrib modules follow the same pattern as external solutions
2. **Self-contained**: Each module can be understood, tested, and potentially extracted independently
3. **Clear boundaries**: Obvious what is framework core vs contrib vs solution code
4. **Selective import**: Solutions import only what they need
5. **Familiar pattern**: Developers learn one architecture pattern for both solutions and contrib modules
6. **Standalone capable**: Modules with `deploy/` can run independently for testing or as microservices

### Negative

1. **Deeper nesting**: More directories than a flat structure
2. **Migration effort**: Existing CEAP code must be relocated
3. **Potential duplication**: Some boilerplate in each module's structure

### Neutral

1. **Tests co-located**: Different from some projects that have top-level `tests/` directory, but consistent with existing Julee conventions

## Alternatives Considered

### 1. Flat Contrib Structure

```
julee/contrib/
├── ceap.py
└── ontology_mapper.py
```

**Rejected**: Doesn't scale. Can't support modules with multiple use cases, domain models, and infrastructure implementations.

### 2. Tests in Separate Top-Level Directory

```
tests/
└── contrib/
    └── ceap/
```

**Rejected**: Breaks with existing Julee convention of co-located tests. Tests wouldn't ship with the module.

### 3. Contrib as Separate Package

Publish `julee-contrib-ceap` as separate PyPI packages.

**Rejected for now**: Adds release complexity. Can revisit if modules become large enough to warrant separate versioning.

### 4. Shared Utilities Within Contrib

```
julee/contrib/
├── _shared/
│   └── testing.py
├── ceap/
└── ontology_mapper/
```

**Rejected**: Would create a shadow framework. Any utilities needed by multiple contrib modules belong in the framework core (`julee.util`).

## References

- [Issue #21: Refactor contrib modules](https://github.com/pyx-industries/julee/issues/21)
- [Julee Architecture Documentation](../architecture/framework.rst)
- [Julee Solution Architecture](../architecture/solutions/index.rst)
- [Contrib Modules Documentation](../architecture/solutions/contrib.rst)
