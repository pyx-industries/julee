# ADR 006: Code-Outward Documentation

## Status

Superseded in part by [ADR 012](012-framework-and-kits.md)

The principle stands: docstrings are the documentation, a solution's own
content is projected rather than restated, and doctrine compliance is what
makes the projection reliable. What ADR 012 removed is the thing this ADR
projects *through*.

**Framework bounded contexts are gone.** Section 2 tabulates `julee.core`,
`julee.hcd` and `julee.c4` as three viewpoints the framework knows in
advance. ADR 012 took the domain out of the kernel: HCD and C4 are kits, and
the projection into documentation is a third kit, `julee-viewpoints`, which
adopts both. `julee.core` projects nothing.

**A viewpoint is now declared, not known.** A kit sets `viewpoint = True` on
its manifest (ADR 012, section 5) and `julee.core.kits.viewpoint_slugs()`
reads it from the kits a solution has adopted. The framework has no list. A
solution that adopts no viewpoint kit has no viewpoints, and one that writes
its own gets them without asking the framework's permission.

**Sections 1, 3 and 7 were never built**, and are recorded here as intent
rather than as description. There is no directive that projects a solution's
instances of a kernel concept; there is no per-entity template selected by
module path; the extensions do not document themselves. What was built
instead is a contribution point: a kit offers Sphinx extensions at
`sphinx.extension`, and `julee.core.kits.sphinx_extensions()` collects them
from the adopted kits. That is composition, not template dispatch, and it
solves a problem this ADR did not have — a framework owning hcd and c4 needs
no way for a stranger to register a directive.

**Section 6 is withdrawn.** "Delete `docs/architecture/` after migrating
valuable editorial content INTO source docstrings" is not the estate's
practice and is not wanted. `docs/` is written and owned, `architecture/`
belongs to it, and prose that explains a decision to a reader is not
redundant with a docstring that documents a callable to a user of it.
Generated API documentation sits beside hand-written architecture; neither
replaces the other.

**Sections 4 and 5 hold.** Directives wrap read use cases and templates
compose them; Sphinx extensions are infrastructure rather than bounded
contexts, which `julee.core.doctrine.rules.boundary` now enforces.

What remains genuinely open is how this relates to [ADR
015](015-semantics-as-claims.md). This ADR imagined projection inside a
framework that owned hcd and c4, where naming another context's class cost
nothing. Once they became separate distributions, that became a claim across
a kit boundary, and ADR 015 answers it with `semantics.toml` — data a kit
publishes and a solution accepts, rather than a relation one kit asserts
about another's model. This ADR predates the boundary existing and says
nothing about it.

The sections below are kept as the record of the original decision.

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
```jinja
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
