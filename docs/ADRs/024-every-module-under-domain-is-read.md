# ADR 024: Every Module Under `domain/` Is Read

## Status

Draft

## Date

2026-10-02

## Context

ADR 023 made every directory under `domain/` one that doctrine reads: a
directory named for a kind holds that kind, and any other is an area.
Three things under `domain/` were still outside it.

**A module directly under `domain/`.** No family read it. The simplest
domain a bounded context can have is a module or two:

    domain/
    ├── invoice.py
    └── payment.py

Doctrine read nothing in it, and a context with nothing else was not
found as a bounded context at all.

**A kind that is a module.** A kind was a directory. A context with two
repository protocols had to make a package to put them in, though to
anything that imports it `repositories.py` and `repositories/` are the
same thing.

**An exception.** A bounded context had nowhere to declare one that
doctrine would accept:

| Declared in | Doctrine |
|-------------|----------|
| `domain/models/` or an area | Objects: it is neither an entity nor a value object |
| `usecases/` | Reads it as a use case (ADR 020), and objects to its name and shape |
| `dtos/` | Objects: it is not a pydantic model (ADR 022) |
| A module directly under `domain/` | Reads nothing |

The kits never met this, because they declare no exception and raise
`ValueError`. A solution that tells "no such invoice" from "that invoice
is already paid" declares exceptions, and keeps them with its domain.

## Decision

**Every module under `domain/` is read, and its name says as what.**

- **A module named for a kind holds that kind**, as a directory of the
  name does. `domain/repositories.py` is read as `domain/repositories/`
  is, and `domain/billing/oracles.py` as `domain/billing/oracles/` is.

- **`errors` is a kind**, the ninth. It holds the exceptions the domain
  declares, and a class in it is an exception: a subclass of
  `Exception`.

- **Any other module is read as entities**, whether `domain/` holds it
  or an area does. `domain/` is the outermost area.

So a context packages its domain as much as it needs to and no more.
Each of these is read, and a context may mix them:

    domain/                 domain/                  domain/
    ├── invoice.py          ├── models/              ├── billing/
    ├── repositories.py     ├── repositories/        │   ├── invoice.py
    └── errors.py           └── errors/              │   ├── repositories/
                                                     │   └── errors.py
                                                     └── shipping/

Exceptions are a kind under `domain/`, and not something `usecases/`
holds, because every ring may import the domain. A use case raises one,
an adapter raises one when what it wraps refuses, and an application
catches one, with no further permission to import. Declared in
`usecases/`, an adapter could never raise it.

What lies beneath a kind directory belongs to the kind, as before.
`domain/models/errors.py` is a module of models.

## Consequences

- The parser has an `errors` family: every class in a directory or a
  module named `errors` under `domain/`, in an area or not.

- A class in `errors` that is not an exception is objected to. It is
  judged by importing it, so an exception built on a base of the
  context's own is known to be one.

- An exception declared among the entities is still objected to, and
  the objection says it belongs in `errors`.

- A port in a module named for its kind is held to the port rules, and
  such a module is a place a port may be declared.

- A package whose domain is a single module is found as a bounded
  context.

- Discovery asks whether a layer has a module doctrine would read. A
  kind directory holding only test files is therefore no longer a layer
  being there.

- `julee doctrine census` reports a class in any module under `domain/`
  against the family that read it, and lists what else such a module
  declares as passed over.

- No kit has a module directly under `domain/`, a module named for a
  kind, or an exception class. The kits' families are what they were.

### What this does not reach

A handler in `domain/handlers.py`. It is read as a handler, and the
rule that a handler protocol sits in a file named `*_handler.py` then
objects to it. That rule asks for one handler to a file, which a module
called `handlers` is not.

A module and a directory of one name side by side, `errors.py` beside
`errors/`. Python imports the package and never the module. Doctrine
reads both.

An exception declared in `usecases/` or in `infrastructure/`. The first
is read as a use case and objected to. The second is in no family.

Who may raise or catch what. This says where an exception is declared.

Entities and values kept together in one module, which ADR 023 already
leaves as it finds.

## Relationship to earlier ADRs

- **ADR 001** laid out `domain/` as directories by kind. That layout is
  read as it was.
- **ADR 002** is applied: a class is found by where it sits, and where
  it sits may now be a module.
- **ADR 016** gave each driven port a directory. A module of the same
  name is that port's too.
- **ADR 020** and **ADR 022** did for `usecases/` and `dtos/` what this
  does for `errors`: every class there is a member, and one rule says
  what a member must be.
- **ADR 023** read every directory under `domain/`. This reads every
  module, and withdraws the exception ADR 023 recorded for a module
  directly under `domain/`.
