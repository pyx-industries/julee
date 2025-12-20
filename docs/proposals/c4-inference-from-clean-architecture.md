# Enhancement Proposal: C4 Inference from Clean Architecture Idioms

## Summary

Extend sphinx_c4 to automatically infer C4 architectural elements from the
conventions established by Julee's clean architecture patterns. Rather than
manually defining every software system, container, component, and relationship,
the extension would derive them from code structure, AST analysis, and existing
HCD entities.

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

## Concept

### The Mapping

Clean architecture idioms map naturally to C4 levels:

```
Clean Architecture          →  C4 Model
─────────────────────────────────────────────────────
Solution repository         →  Software System
External service protocols  →  External Systems
docker-compose services     →  External Systems

apps/api/                   →  Container (API)
apps/cli/                   →  Container (CLI)
apps/worker/                →  Container (Worker)
src/{bounded-context}/      →  Container (per domain)

domain/models/ classes      →  Components (Entities)
use_cases/ classes          →  Components (Use Cases)
domain/repositories/        →  Components (Protocols)
domain/services/            →  Components (Protocols)
worker/pipelines/           →  Components (Pipelines)

import statements           →  Relationships
```

### Integration with HCD

The HCD extension already establishes relationships between documentation
entities and code:

| HCD Entity | C4 Mapping |
|------------|------------|
| Accelerator | Container (bounded context) |
| Application | Container (entry point) |
| Story → Pipeline | Component relationship |
| Integration | External System |

This creates a bridge: HCD captures the *why* and *who*, C4 captures the *what*
and *how*, and both can be inferred from the same codebase.

## Proposed Capabilities

### 1. Inferred Software System

Derive the top-level software system from the solution itself:

```rst
.. infer-software-system::
   :name: RBA Platform
   :description: From pyproject.toml or __init__.py docstring
```

Would produce a `define-software-system::` equivalent by reading project
metadata.

### 2. Inferred External Systems

Discover external systems from multiple sources:

- **Service protocols**: Classes in `domain/services/` that wrap external APIs
- **Docker Compose**: Services marked as external (databases, message queues)
- **Settings/Environment**: URLs and credentials pointing to external services
- **Integration manifests**: Already captured by HCD

```rst
.. infer-external-systems::
   :from: docker-compose, service-protocols, integrations
```

### 3. Inferred Containers

Detect containers from directory structure:

```rst
.. infer-containers::
   :apps-dir: apps/
   :bounded-contexts: src/
```

Would discover:
- `apps/api/` → Container "API" (technology: FastAPI)
- `apps/worker/` → Container "Worker" (technology: Temporal)
- `src/vocabulary/` → Container "Vocabulary" (bounded context)
- `src/assessment/` → Container "Assessment" (bounded context)

### 4. Inferred Components

Use existing AST introspection (BoundedContextInfo) to discover components:

```rst
.. infer-components::
   :bounded-context: vocabulary
```

Would use the existing `parse_bounded_context()` function to find:
- Entities from `domain/models/`
- Use cases from `use_cases/`
- Repository protocols from `domain/repositories/`
- Service protocols from `domain/services/`

### 5. Inferred Relationships

Analyse import statements to discover dependencies:

```rst
.. infer-relationships::
   :bounded-context: vocabulary
   :depth: 2
```

Would parse imports to find:
- UseCase imports RepositoryProtocol → "reads from / writes to"
- UseCase imports ServiceProtocol → "uses"
- Pipeline imports UseCase → "executes"
- API route imports UseCase → "exposes"

### 6. Hybrid Approach

Allow mixing inferred and explicit definitions:

```rst
.. infer-container-diagram::
   :software-system: rba

.. define-container:: legacy-system
   :system: rba
   :external: true
   :description: Manually defined because not in our codebase
```

Inferred elements could be augmented or overridden by explicit definitions.

## Implementation Considerations

### Extending Existing Infrastructure

The `sphinx_hcd` extension already has:

- **AST parser** (`parsers/ast.py`): Extracts classes from Python files
- **BoundedContextInfo model**: Captures entities, use cases, protocols
- **Directory scanning**: `scan_bounded_contexts()` function
- **Code info repository**: Stores introspected data

This infrastructure could be extended rather than duplicated.

### New Parsers Needed

| Parser | Purpose |
|--------|---------|
| Import graph analyser | Build dependency graph from `import` statements |
| Docker Compose parser | Extract services, technologies, relationships |
| Settings scanner | Find external service references |
| Route/command scanner | Map API routes and CLI commands to use cases |

### Relationship Inference Heuristics

Import analysis needs heuristics to determine relationship types:

```python
# Heuristic examples
if imported_class.endswith("Repository"):
    relationship_type = "reads from / writes to"
elif imported_class.endswith("Service"):
    relationship_type = "uses"
elif imported_class.endswith("UseCase"):
    relationship_type = "executes"
```

### Caching and Performance

AST parsing can be expensive. Consider:

- Caching parsed results between Sphinx builds
- Incremental updates when only some files change
- Lazy loading of detailed component info

## Open Questions

### Granularity Control

How much should be inferred vs explicit?

- **Minimal inference**: Only suggest, human writes definitions
- **Full inference**: Generate everything, human overrides
- **Hybrid**: Infer structure, human adds descriptions

### Diagram Generation

Should inferred elements automatically generate diagrams?

- PlantUML from inferred containers and relationships
- Or just populate the C4 repositories for manual diagram directives

### Accuracy vs Completeness

Import analysis may miss runtime dependencies (dependency injection, dynamic
imports). How to handle:

- Warn about incomplete analysis?
- Allow manual supplementation?
- Integrate with DI container configuration?

### Cross-Repository Systems

For solutions that span multiple repositories:

- How to reference external systems defined elsewhere?
- Shared C4 element registries?

### Versioning and History

C4 diagrams often need to show:

- Current state vs target state
- Evolution over time

How does inference interact with versioned architecture documentation?

## Relationship to Existing Work

### sphinx_hcd Accelerator Scanning

The `define-accelerator::` directive already does bounded context introspection:

```python
# From accelerator.py
code_info = hcd_context.code_info_repo.get(accelerator.code_dir)
if code_info:
    # Render entities, use cases, protocols from introspection
```

C4 inference would use the same data but render it as C4 elements.

### HCD → C4 Bridge

The relationship between HCD and C4 could be explicit:

| HCD | C4 |
|-----|-----|
| Accelerator | maps to Container |
| Application | maps to Container |
| Integration | maps to External System |
| Story.pipeline | maps to Component |

This bridge would allow navigation between perspectives:
- "Which container implements this accelerator?"
- "Which stories are satisfied by this component?"

## Success Criteria

A successful implementation would:

1. **Reduce manual C4 authoring** for well-structured Julee solutions
2. **Stay current automatically** as code evolves
3. **Integrate with HCD** for traceability across perspectives
4. **Support hybrid mode** for elements that can't be inferred
5. **Generate useful diagrams** without manual layout work

## Next Steps

1. **Discuss and refine** this proposal
2. **Prototype import analysis** to validate relationship inference
3. **Design the directive API** for inference directives
4. **Consider ADR** once approach is agreed

## References

- ADR 001 (julee): Contrib Module Layout
- ADR 003 (julee): Sphinx HCD Extensions Package
- ADR 001 (rba): Use Julee Solution Architecture
- ADR 002 (rba): Documentation Organisation
- [C4 Model](https://c4model.com/) - Simon Brown
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) - Robert C. Martin
