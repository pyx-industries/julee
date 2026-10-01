# ADR 021: A Name Does Not Hide a Class from Doctrine

## Status

Draft

## Date

2026-10-02

## Context

ADR 002 keeps finding apart from naming: doctrine finds an artifact by
the directory it sits in, and a name used to find things is a filter
that drops what it misses without saying so. ADR 020 applied that to
use cases and named two filters it left alone. Both are in the class
parser, so both act on every family: entities, values, ports and use
cases alike.

- **A class whose name begins `Test` was not read.** The filter was
  there to keep tests out, and tests are already kept out by the file
  they are in: a name beginning `test_`, or a place under `tests/`. What
  the class filter still did was hide real classes. A domain can have a
  `TestResult` or a `Testimonial`.

- **A module whose name begins with an underscore was not read.** The
  underscore says private to a reader. To doctrine it said absent.

Neither omission was reported. Run against a solution with one entity
and one use case, `julee doctrine verify` gave these results before
this ADR:

| Solution | Doctrine |
|----------|----------|
| A mutable entity named `ExamResult` | Objects: an entity is frozen |
| The same entity named `TestResult` | Passes |
| A helper class in `usecases/helpers.py` | Objects: a class in `usecases/` is a use case (ADR 020) |
| The same helper in `usecases/_helpers.py` | Passes |

So a name could turn an objection into a pass. The second pair is a way
round ADR 020 that takes one character.

No class in `julee-c4`, `julee-ceap`, `julee-hcd` or `julee-polling`
was hidden by either filter.

## Decision

**A class is read whatever it is called, and so is the module it is
in.** Doctrine leaves out a test by where the test is, and nothing by
its name.

- The class parser no longer drops a class whose name begins `Test`.
- It no longer skips a module whose name begins with an underscore.

One module is still not read for classes: a package's `__init__.py`.
It is left out by its whole name rather than by a prefix, and it is the
exception this ADR leaves standing. ADR 019 has it importing nothing it
does not use, and a class declared in one is not read.

A private module is still private to whoever imports it. That is a
convention between modules, and doctrine is not one of them: it reads
what a bounded context contains.

## Consequences

- A class named `Test*` in a file that is not a test is a member of
  whatever family its directory makes it, and is held to that family's
  rules.

- A class in `_something.py` is read like any other. In `usecases/` it
  is a use case; in `domain/models/` it is an entity.

- The rule that every file doctrine reads must be readable follows the
  parser, so it now asks an underscore module to parse and still does
  not ask a package's `__init__.py`.

- Names a use case module imports are collected from underscore modules
  too, so a use case there finds its request and response.

- `julee doctrine census` reports such a class as claimed by its
  family. A class it lists as unclaimed in a family directory can now
  only be one in a package's `__init__.py`; the functions and bindings
  it lists there are unchanged.

- A solution that kept classes in underscore modules, or named a domain
  class `Test*`, sees each one checked the first time it runs this, and
  an objection for each that does not comply.

### What this does not reach

A class declared in a package's `__init__.py` is still not read.

Pipeline discovery, which is a separate reader, still skips an
underscore module directly under `apps/worker/` when it has no
`pipelines.py` to go by.

## Relationship to earlier ADRs

- **ADR 002** is applied: these were the last two names the class
  parser used to decide what to read.
- **ADR 020** named both filters and left them for this decision.
- **ADR 019** is why an `__init__.py` is expected to hold little, and is
  not a reason it could not hold a class.
