# ADR 005: Doctrine and Policy Separation

## Status

Draft

## Date

2025-12-28

## Context

ADR 002 established that "tests ARE the doctrine" - test files both express and enforce architectural rules. This ADR extends ADR 002 by introducing a distinction between universal axioms (doctrine) and adoptable strategic choices (policy). ADR 002 establishes the mechanism; this ADR refines what qualifies as doctrine versus what should be a separately-adoptable policy.

This has worked well for the julee framework itself, but a gap has emerged: not all rules are equal.

When a developer creates a new solution using julee, they run `julee-admin doctrine verify` against their codebase. Currently, this runs all doctrine tests, including rules that are specific to julee's own structure (Sphinx documentation requirements, MCP framework usage, test organization patterns).

This conflates two distinct categories:

1. **Universal axioms** that define what julee concepts ARE (entities must be PascalCase, use cases must have execute())
2. **Strategic choices** that julee makes about HOW to implement things (use Sphinx for docs, organize tests in tests/ directories)

A solution developer should be bound by the axioms (they're using julee concepts), but strategic choices should be explicitly adopted, not implicitly inherited.

## Definitions

### Doctrine

**Doctrine is axiomatic and universal.** It defines the essential nature of julee concepts. If a rule is doctrine, it applies to ALL julee solutions without exception. There is no opting out.

Doctrine answers: "What makes an Entity an Entity? What makes a UseCase a UseCase?"

Examples of doctrine:
- Entities MUST be PascalCase
- Entities MUST NOT end with UseCase, Request, or Response
- UseCases MUST have an execute() method
- UseCases MUST have matching Request and Response classes
- Repository protocols MUST inherit from Protocol
- Dependencies MUST point inward (Clean Architecture)

If you violate doctrine while claiming to build a julee solution, you have a bug.

### Policy

**Policy is strategic and adoptable.** It represents choices about how to implement solutions. Policies can be adopted or skipped. They are enforced only when explicitly or implicitly adopted.

Policy answers: "How should we document? How should we organize tests? What frameworks should we use?"

Examples of policy:
- Solutions should have Sphinx documentation (`sphinx-documentation`)
- Tests should live in tests/ directories (`test-organization`)
- MCP apps should use create_mcp_server() (`mcp-framework`)
- Temporal workflows should follow pipeline patterns (`temporal-pipelines`)

Policies become binding through adoption.

### Library vs Framework

**Library**: Code you call. You import julee modules and use them in your own structure. You are not claiming to be a "julee solution." Running `julee-admin doctrine verify` will report violations, but they are informational - you're not bound by julee's patterns.

**Framework**: Code that calls you. You structure your solution according to julee's patterns (bounded contexts, use cases, Clean Architecture layers). You ARE a julee solution. Doctrine violations are bugs. Adopted policy violations are bugs.

The distinction is signaled by the presence of `[tool.julee]` in pyproject.toml:
- No `[tool.julee]` section: library usage (informational verification)
- Has `[tool.julee]` section: framework usage (violations are bugs)

### Framework-Default Policies

Some policies are adopted by default when you declare yourself a julee solution. These represent julee's opinionated choices that have proven valuable. You can opt out with explicit configuration, but the default is adoption.

Framework-default policies become doctrine for julee solutions through inheritance:

```
Core Doctrine (axioms)
       │
       │ always applies
       ▼
Framework-Default Policies
       │
       │ applies to [tool.julee] solutions
       │ (can opt out explicitly)
       ▼
Solution Policies (additional choices)
       │
       │ applies to this solution only
       ▼
Verified Solution
```

## Decision

### Separate Doctrine from Policy

Refactor the current `core/doctrine/` directory to contain only axiomatic rules. Move strategic choices to a new `core/policies/` structure.

**Doctrine (axioms) - `core/doctrine/`:**
- `test_entity.py` - Entity axioms
- `test_use_case.py` - UseCase axioms
- `test_request.py` - Request axioms
- `test_response.py` - Response axioms
- `test_repository_protocol.py` - RepositoryProtocol axioms
- `test_service_protocol.py` - ServiceProtocol axioms
- `test_bounded_context.py` - BoundedContext axioms (structural only)
- `test_dependency_rule.py` - Clean Architecture axioms

**Policies (strategic) - `core/policies/`:**
- `sphinx_documentation/` - Documentation requirements
- `test_organization/` - Test structure requirements
- `mcp_framework/` - MCP implementation patterns
- `temporal_pipelines/` - Temporal workflow patterns

### Policy Structure

Each policy is a package containing:

```
core/policies/sphinx_documentation/
├── __init__.py           # Policy metadata
├── policy.py             # Policy definition
└── test_compliance.py    # Compliance tests
```

Policy definition:

```python
# core/policies/sphinx_documentation/policy.py
from dataclasses import dataclass

@dataclass
class SphinxDocumentationPolicy:
    """Solutions must have buildable Sphinx documentation.

    This policy ensures all julee solutions have consistent,
    buildable documentation using Sphinx with the standard
    julee theme and structure.
    """
    slug: str = "sphinx-documentation"
    name: str = "Sphinx Documentation"
    framework_default: bool = True  # Adopted by default for julee solutions
    requires: tuple[str, ...] = ()  # No dependencies on other policies
```

### Configuration Schema

```toml
# pyproject.toml

[tool.julee]
# Presence of this section = "I am a julee solution"
# Framework-default policies automatically apply

# Opt into additional policies:
policies = [
    "postgresql-patterns",
    "async-repositories",
]

# Opt out of framework defaults:
skip_policies = [
    "temporal-pipelines",  # We don't use Temporal
]
```

### CLI Changes

```bash
# Doctrine verification (axioms - always runs all)
julee-admin doctrine verify
julee-admin doctrine verify --target /path/to/solution
julee-admin doctrine show
julee-admin doctrine list

# Policy management
julee-admin policy list                    # All available policies
julee-admin policy list --adopted          # Policies in effect for this solution
julee-admin policy verify                  # Verify adopted policies
julee-admin policy verify --all            # Verify all policies (informational)
julee-admin policy adopt <slug>            # Add to pyproject.toml
julee-admin policy skip <slug>             # Add to skip_policies
```

### Verification Output

```
$ julee-admin doctrine verify

DOCTRINE (8 areas, 24 rules):
  Entity .......................... 4/4 passed
  UseCase ......................... 5/5 passed
  Request ......................... 4/4 passed
  Response ........................ 3/3 passed
  RepositoryProtocol .............. 3/3 passed
  ServiceProtocol ................. 4/4 passed
  BoundedContext .................. 3/3 passed
  DependencyRule .................. 4/4 passed

All doctrine checks passed.

$ julee-admin policy verify

POLICIES (framework defaults):
  sphinx-documentation ............ passed
  test-organization ............... passed
  mcp-framework ................... FAILED (2 violations)
  temporal-pipelines .............. skipped (not applicable)

POLICIES (adopted):
  postgresql-patterns ............. passed

2 policy violations found. Run with --verbose for details.
```

### Domain Model Extension

Add Policy entity to `core/entities/`:

```python
# core/entities/policy.py
"""A Policy is an adoptable strategic choice.

Unlike Doctrine (axiomatic, universal), Policies are opt-in
strategic decisions a solution can make. Framework-default
policies apply automatically to julee solutions but can be
explicitly skipped.

Policy adoption is transitive: if you declare yourself a julee
solution, you inherit framework-default policies as binding
requirements unless explicitly skipped.
"""

from dataclasses import dataclass, field

@dataclass
class Policy:
    """An adoptable strategic choice with compliance tests."""

    slug: str
    name: str
    description: str
    framework_default: bool = False
    requires: tuple[str, ...] = field(default_factory=tuple)
    test_module: str = ""  # Path to compliance tests
```

## Consequences

### Positive

1. **Clear semantics**: Doctrine is non-negotiable; policies are choices
2. **Flexibility for solutions**: Solutions can adopt julee patterns incrementally
3. **Framework evolution**: New policies can be added without breaking existing solutions
4. **Explicit inheritance**: Framework-default policies make the "julee way" clear
5. **Escape hatches**: Solutions can skip policies with explicit configuration
6. **Better DX**: `julee-admin` output distinguishes axiom violations from policy violations

### Negative

1. **Migration effort**: Existing doctrine tests must be audited and categorized
2. **More concepts**: Users must understand doctrine vs policy distinction
3. **Configuration complexity**: More options in pyproject.toml

### Neutral

1. **Backward compatibility**: Existing julee solutions implicitly adopt all framework-default policies, so behavior is unchanged until they explicitly skip something

## Implementation Plan

1. Create `core/entities/policy.py` with Policy entity
2. Create `core/policies/` directory structure
3. Audit existing doctrine tests, move policy-like tests to policies/
4. Update `julee-admin doctrine` to only run axiom tests
5. Implement `julee-admin policy` commands
6. Update conftest.py to support --target for external solutions
7. Add pyproject.toml configuration parsing
8. Update ADR 002 to reference this ADR for the doctrine/policy distinction

## References

- ADR 002: Doctrine Test Architecture (establishes "tests ARE doctrine")
- RFC 2119: Key words for use in RFCs to Indicate Requirement Levels
- Clean Architecture (Robert C. Martin)
- `core/doctrine/` - Current doctrine tests (to be refactored)
