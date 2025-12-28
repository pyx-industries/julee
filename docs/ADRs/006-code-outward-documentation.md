# ADR 006: Code-Outward Documentation

## Status

Draft

## Date

2025-12-28

## Context

Julee documentation exists in parallel forms: hand-written RST and autodoc-generated
API docs. This creates drift, duplication, and maintenance burden.

The doctrine system (ADR 002) establishes that tests ARE the specification. The same
principle applies to documentation: **docstrings ARE the documentation**.

## Decision

### 1. Framework = Information Architecture, Content = Solution

The julee framework provides semantic scaffolding; solutions provide content.

Every entity in `julee.core.entities/` serves two purposes:
- **Docstring defines the concept** (what IS an Entity?)
- **Directive projects solution instances** (list THIS solution's entities)

The pattern recurses:
```
Concept (julee.core.entities.*)
  → lists interfaces (solution's {bc}/repositories/, {bc}/services/)
    → links to implementations ({bc}/infrastructure/)
      → links to applications using them (via DI containers)
```

This creates a navigable dependency graph through documentation.

### 2. Viewpoints Are Projections Through Framework BCs

Framework bounded contexts become documentation viewpoints:

| Framework BC | Viewpoint | Projects |
|--------------|-----------|----------|
| `julee.core` | Technical Framework | Entities, use cases, protocols |
| `julee.hcd` | Human-Centred Design | Personas, journeys, stories |
| `julee.c4` | Architecture | Systems, containers, components |

**Solution documentation** screams its domain—BCs at root alongside viewpoints.
Consider a SPECTRE-like Evil World Domination Enterprise:

```
/
├── Henchmen and Other Minions       ← Solution BC
├── Very Large Kites                 ← Solution BC
├── Warfare and Politics             ← Solution BC
├── Counter-intelligence             ← Solution BC
├── Revenge and Extortion            ← Solution BC
├── Human Centred Design             ← Viewpoint (julee.hcd projection)
├── Architecture                     ← Viewpoint (julee.c4 projection)
└── Technical Framework              ← Viewpoint (julee.core projection)
```

**Framework documentation** screams software engineering—because its domain IS
the viewpoints. The framework BCs (core, hcd, c4) happen to BE the viewpoints.

Same semantic scaffolding. Solutions inherit the framework, thus the information
architecture. Their BCs appear at root level; viewpoints project their content
through framework lenses.

### 3. Bespoke Templates Per Entity Type

Leverage autodoc with entity-specific templates:

1. **Doctrine compliance guarantees structure** - If code passes doctrine, we KNOW what it is
2. **Template selection by module path** - `*/entities/*.py` → entity template
3. **Each template renders docstring + appropriate directives**

```
julee.hcd.entities.story.Story
  ↓ doctrine says this is an HCD Story entity
  ↓ autodoc selects story_template.rst
  ↓ template renders: docstring + story-hub directive
  ↓ rendered page shows: concept definition + this solution's related content
```

Docstrings don't contain directives—templates add them based on doctrine-guaranteed structure.

### 4. Directives Wrap Use Cases, Templates Handle Presentation

```
Directive granularity = Use Cases
Template granularity = Entity types (presentation)
```

**Directives** are thin wrappers:
- `list-stories` → wraps `ListStoriesUseCase`
- `get-relationships` → wraps `GetRelationshipsUseCase`

**Templates** compose directives for presentation:
```jinja2
{{ docstring }}

This Solution's Stories
-----------------------
.. list-stories::
```

This keeps directives reusable and puts presentation logic where it belongs.

### 5. Sphinx Apps Are Infrastructure

Sphinx extensions are infrastructure, not bounded contexts:
- Call **Read use cases** from framework BCs
- Wire use cases together (composition root)
- Handle presentation via directives and templates
- RST serialization is presentation, not domain logic

### 6. Code Exists → Autodoc; Code Doesn't Exist → Design Doc

```
docs/
├── index.rst             ← Entry point, links into api/
├── api/                  ← THE documentation (generated)
└── design/               ← ONLY for unimplemented features
    └── future_feature.rst  ← Deleted once implemented
```

Hand-written RST for implemented code is redundant. Delete `docs/architecture/`
after migrating valuable editorial content INTO source docstrings.

### 7. Self-Documenting Infrastructure

The sphinx extensions document themselves using the same patterns they provide,
demonstrating the information architecture pattern.

## Consequences

### Positive

1. **No drift** - Documentation generated from code cannot diverge
2. **Navigable graph** - Concept → interface → implementation → application
3. **Automatic updates** - New code → new documentation
4. **Single source** - Docstrings are canonical; RST is redundant
5. **Doctrine-enabled** - Compliance guarantees introspection works

### Negative

1. **Migration effort** - RST content must migrate to docstrings
2. **Template complexity** - Bespoke templates per entity type
3. **Docstring discipline** - Developers must write rich docstrings

### Neutral

1. **API docs become primary** - `api/` section IS the documentation

## Key Design Principles

1. **Docstrings ARE Documentation** - Autodoc renders them; RST duplicates them
2. **Introspection Over Enumeration** - Catalog directives, not hard-coded lists
3. **Doctrine Compliance Enables Projection** - Conventions make introspection reliable
4. **Code Exists → Autodoc** - Hand-written RST is only for unimplemented features

## References

- ADR 002: Doctrine Test Architecture
- ADR 005: Doctrine and Policy Separation
