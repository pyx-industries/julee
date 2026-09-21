# ADR 014: The Use Case Package Is `usecases`

## Status

Accepted

## Date

2026-09-21

## Context

[ADR 001](001-contrib-layout.md) laid out a bounded context with its application business rules in a package named `use_cases/`, and the framework, its contrib modules and its doctrine followed. Solutions built on julee's ideas have settled on `usecases/`, one word, beside `domain/`, `adapters/` and `apps/`. The two spellings mean the same thing, and the difference is not cosmetic: doctrine finds a bounded context's use cases by one path, `USE_CASES_PATH`, so a solution that spells it the other way has use cases doctrine cannot see. A rule that silently checks nothing is the failure the layout constants had until they were corrected to ADR 001's `domain/` layout.

The owner decided the name is `usecases`, everywhere.

## Decision

The package that holds a bounded context's use cases is named `usecases`.

- `USE_CASES_PATH` is `("usecases",)`. It remains the one place the name is written; the doctrine checks that looked for the directory by a literal now read the constant.
- julee's own packages are renamed: `julee.core.usecases`, `julee.contrib.ceap.usecases`, `julee.contrib.polling.usecases`, and, in the viewpoints kit, `julee_viewpoints.sphinx_hcd`'s `domain/usecases`.
- The generated CRUD use cases are written to `.generated/usecases/` (ADR 008).

What does not change: Python identifiers that mean "the use cases" rather than the package, such as `BoundedContextInfo.use_cases` and `StructuralMarkers.has_domain_use_cases`; the layer label `has_layer("use_cases")`, which belongs to the same vocabulary as `"models"` and is not a directory name; the `UseCase` class suffix; and the documentation page `use_cases.rst`.

## Relationship to earlier ADRs

- **ADR 001** is amended: where it writes `use_cases/`, read `usecases/`. Its layout is otherwise unchanged.
- **ADR 002**, **ADR 008** and **ADR 010** mention the old name in examples and directory trees. They are left as written, as the record of what was decided then; this ADR governs the name.

## Consequences

### Positive

1. One spelling across julee and the solutions that follow it, so a solution's use cases are visible to doctrine without configuration.
2. The name is written once, in `USE_CASES_PATH`.

### Negative

1. A breaking change for any solution that imports `julee.core.use_cases` or lays its contexts out with `use_cases/`. Such a solution renames the package, or its use cases stop being checked.
2. Earlier ADRs show the old name in their examples.

## Alternatives Considered

**Make the layer path configurable per solution.** Rejected. It keeps two spellings alive for good, and it moves a convention doctrine exists to hold into configuration that each solution can get wrong.

**Keep `use_cases` and have solutions rename.** Rejected by the owner.
