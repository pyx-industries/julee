# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Julee framework.

## What is an ADR?

An ADR is a document that captures an important architectural decision made along with its context and consequences.

```{toctree}
:hidden:
:maxdepth: 1

001-contrib-layout
002-doctrine-test-architecture
003-workflow-orchestration-handlers
004-execution-agnostic-use-cases
005-doctrine-and-policy
006-code-outward-documentation
007-semantic-relations
008-generic-crud-use-cases
009-repository-service-distinction
010-apps-layer-architecture
011-canonical-julee-line
012-framework-and-kits
013-sphinx-hcd-extensions
014-usecases-package-name
015-semantics-as-claims
016-driven-ports
017-a-usecase-does-not-log
018-a-value-object-has-no-identity
019-an-init-imports-nothing-it-does-not-use
020-a-class-in-usecases-is-a-use-case
021-a-name-does-not-hide-a-class
022-a-class-in-dtos-is-a-message
```

## ADR Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| [001](001-contrib-layout.md) | Contrib Module Layout | Draft | 2025-12-09 |
| [002](002-doctrine-test-architecture.md) | Doctrine Test Architecture | Draft | 2025-12-24 |
| [003](003-workflow-orchestration-handlers.md) | Workflow Orchestration via Handler Services | Draft | 2025-12-28 |
| [004](004-execution-agnostic-use-cases.md) | Execution-Agnostic Use Cases | Draft | 2025-12-28 |
| [005](005-doctrine-and-policy.md) | Doctrine and Policy Separation | Draft | 2025-12-28 |
| [006](006-code-outward-documentation.md) | Code-Outward Documentation | Draft | 2025-12-28 |
| [007](007-semantic-relations.md) | Semantic Relations Decorator Pattern | Superseded by [015](015-semantics-as-claims.md) | 2026-01-07 |
| [008](008-generic-crud-use-cases.md) | Generic CRUD Use Case Generators | Draft | 2026-01-07 |
| [009](009-repository-service-distinction.md) | Repository vs Service Protocol Distinction | Superseded by [016](016-driven-ports.md) | 2026-01-07 |
| [010](010-apps-layer-architecture.md) | Apps Layer and Reserved Words Architecture | Draft | 2026-01-07 |
| [011](011-canonical-julee-line.md) | Master Is the Canonical Julee Line | Accepted | 2026-09-21 |
| [012](012-framework-and-kits.md) | Separating the Framework from Domain Kits | Draft | 2026-09-21 |
| [013](013-sphinx-hcd-extensions.md) | Sphinx HCD Extensions Package | Superseded in part by 012 | 2025-12-11 |
| [014](014-usecases-package-name.md) | The Use Case Package Is `usecases` | Accepted | 2026-09-21 |
| [015](015-semantics-as-claims.md) | Kits Claim, Solutions Decide | Draft | 2026-09-24 |
| [016](016-driven-ports.md) | Naming the Driven Ports | Draft | 2026-09-25 |
| [017](017-a-usecase-does-not-log.md) | A Use Case Does Not Log | Draft | 2026-09-29 |
| [018](018-a-value-object-has-no-identity.md) | A Value Object Has No Identity | Draft | 2026-09-29 |
| [019](019-an-init-imports-nothing-it-does-not-use.md) | An `__init__.py` Imports Nothing It Does Not Use | Accepted | 2026-09-30 |
| [020](020-a-class-in-usecases-is-a-use-case.md) | A Class in `usecases/` Is a Use Case | Draft | 2026-10-02 |
| [021](021-a-name-does-not-hide-a-class.md) | A Name Does Not Hide a Class from Doctrine | Draft | 2026-10-02 |
| [022](022-a-class-in-dtos-is-a-message.md) | A Class in `dtos/` Is a Message | Draft | 2026-10-02 |
