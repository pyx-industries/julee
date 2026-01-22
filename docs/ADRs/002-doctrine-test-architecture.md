# ADR 002: Doctrine Test Architecture

## Status

Draft

## Date

2025-12-24

## Context

Julee is a framework for building AI-powered document processing solutions. Its purpose is to enable organizations to create auditable, traceable, and maintainable AI workflows. To achieve this, solutions must follow a consistent technical architecture that enables:

1. **Digital supply chain transparency**: Every component's origin, purpose, and dependencies are discoverable
2. **Traceability**: The relationship between business requirements and implementation is explicit
3. **Tool integration**: Consistent structure enables automated tooling (documentation generation, dependency analysis, compliance checking)
4. **Maintainability**: Developers can navigate any Julee solution because they all follow the same patterns

The technical architecture is Clean Architecture with strict opinions about code organization. These opinions must be enforced automatically - documentation alone is insufficient because it drifts from reality.

## Decision

**Doctrine is the set of architectural rules that all Julee solutions must follow. Tests ARE the doctrine - they both express and enforce the rules.**

### What Doctrine Covers

Doctrine defines the structural constraints for a valid Julee solution. The categories of doctrine correspond to the entities in the framework's core domain model:

| Domain Entity | Doctrine Enforces |
|---------------|-------------------|
| **Bounded Context** | What constitutes a valid bounded context (domain/models or domain/use_cases required) |
| **Repository Protocol** | Repository interfaces live in domain/, implementations in infrastructure/ |
| **Service Protocol** | Service interfaces live in domain/, implementations in infrastructure/ |
| **Use Case** | Business logic lives in use_cases/, has execute() method taking request/response objects |
| **Infrastructure** | Implementations coupled to external systems live in infrastructure/ or repositories/ |
| **Viewpoint** | HCD and C4 are special bounded contexts that provide architectural views |
| **Contrib** | Batteries-included modules under contrib/ follow the same structure |

### Mechanism: Tests as Enforcement

Doctrine tests live in the framework's shared component and can be run against:

1. **The Julee framework itself** - ensuring the framework follows its own rules
2. **Any Julee solution** - ensuring solutions comply with the architecture

```
shared/tests/domain/use_cases/
└── test_bounded_context_doctrine.py   # Doctrine about bounded contexts
```

Test docstrings express rules using RFC 2119 language (MUST, MAY, MUST NOT):

```python
class TestBoundedContextStructure:
    """Doctrine about bounded context structure."""

    async def test_bounded_context_MUST_have_domain_models_or_use_cases(self, tmp_path):
        """A bounded context MUST have domain/models or domain/use_cases."""
        # Assertions enforce this requirement
```

### Why Tests ARE Doctrine

Traditional approaches separate rule definition from enforcement:

- Documentation states rules
- Tests verify rules
- Rules and tests inevitably diverge

With "tests as doctrine":

- The test docstring IS the rule statement
- The test body IS the enforcement
- There is no drift because they are the same artifact

### Clean Architecture with Strict Opinions

Julee implements Clean Architecture (entities, use cases, interface adapters, frameworks/drivers) with these additional constraints:

1. **Directory structure is prescribed**: `domain/models/`, `domain/repositories/`, `domain/services/`, `domain/use_cases/`
2. **Naming conventions are prescribed**: Bounded context names must not use reserved words
3. **Dependency direction is enforced**: Domain has no dependencies on infrastructure
4. **Interface segregation is enforced**: Protocols in domain/, implementations outside

These strict opinions enable:

- **Automated discovery**: Tools can find all bounded contexts, use cases, etc.
- **Documentation generation**: Consistent structure enables Sphinx AutoAPI
- **Dependency analysis**: Import graph follows predictable patterns
- **Compliance verification**: Run doctrine tests to validate any solution

### Constants as Doctrine Declarations

Magic values referenced by doctrine are declared as module-level constants:

```python
RESERVED_WORDS = frozenset({"core", "contrib", "applications", "docs", "deployment",
                            "shared", "util", "utils", "common", "tests"})
VIEWPOINT_SLUGS = frozenset({"hcd", "c4"})
```

Doctrine tests verify these constants contain expected values. This makes the rules discoverable and the tests self-documenting.

### Three Levels of Tests

| Level | Location | Purpose |
|-------|----------|---------|
| **Doctrine** | `shared/tests/domain/use_cases/test_*_doctrine.py` | Universal rules for all Julee solutions |
| **Framework** | `shared/tests/` (non-doctrine) | Tests specific to framework implementation |
| **Domain** | `{bounded_context}/tests/` | Tests for specific bounded context behavior |

Only doctrine tests use MUST/MAY/MUST NOT language. Other tests are ordinary unit/integration tests.

### Doctrine vs Policy

Not all architectural rules are equal. Some are universal axioms (doctrine) that define what julee concepts ARE. Others are strategic choices (policies) that can be adopted or skipped. See ADR 005 (Doctrine and Policy Separation) for the distinction and how policies are configured.

## Consequences

### Positive

1. **Architectural compliance is verifiable**: Run pytest to check any solution
2. **Single source of truth**: Rules cannot diverge from enforcement
3. **Tool-friendly structure**: Consistent patterns enable automation
4. **Supply chain transparency**: Every component's role is explicit and discoverable
5. **Traceability**: Clear path from business rules (use cases) to implementation (infrastructure)
6. **Progressive disclosure**: Read at docstring level or implementation level

### Negative

1. **Rigidity**: Less flexibility than a permissive framework
2. **Learning curve**: Developers must learn Clean Architecture concepts as they work with the framework and enforced doctrine.

### Neutral

1. **Framework-dependent solutions**: Solutions are tightly coupled to Julee conventions

## Alternatives Considered

### 1. Documentation-Only Architecture

Write architecture rules in markdown, trust developers to follow them.

**Rejected**: Rules drift from reality. No automated verification.

### 2. Runtime Validation

Check architectural constraints at application startup.

**Rejected**: Too late - violations should be caught in CI, not production.

### 3. Linter-Based Enforcement

Create custom linting rules (pylint, ruff) for architecture.

**Rejected**: Complex to maintain. Tests are simpler and more expressive.

### 4. Permissive Framework

Allow solutions to organize code however they want.

**Rejected**: Loses benefits of consistency (tool integration, discoverability, traceability).

## References

- RFC 2119: Key words for use in RFCs to Indicate Requirement Levels
- Clean Architecture (Robert C. Martin)
- `shared/tests/domain/use_cases/test_bounded_context_doctrine.py` - Bounded context doctrine
- `shared/repositories/introspection/bounded_context.py` - Discovery implementation
