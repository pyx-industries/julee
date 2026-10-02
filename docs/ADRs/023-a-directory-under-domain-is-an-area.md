# ADR 023: A Directory Under `domain/` That Names No Kind Is an Area

## Status

Draft

## Date

2026-10-02

## Context

ADR 001 gives a bounded context a `domain/` with a directory for each
kind of class: `models/` for entities, `values/` for value objects
(ADR 018), and one for each driven port (ADR 016). Doctrine finds a
class by the kind directory it sits in (ADR 002).

A context of any size also divides its domain by the part of the
business a class belongs to: billing, shipping. Call that an area.
Doctrine reads a kind directory with everything beneath it, so an area
could already sit below the kind:

    domain/
    ├── models/billing/invoice.py
    └── repositories/billing/invoice.py

That spreads each area across as many directories as there are kinds.
The other order keeps an area together, and makes the business the
first thing a reader of `domain/` sees:

    domain/
    └── billing/
        ├── invoice.py
        └── repositories/invoice.py

Doctrine read nothing in a directory like `domain/billing/`. One rule
noticed it: a package under `domain/` that doctrine read nothing out of
was objected to for being there. That rule was written for a context
that kept one entity in `domain/entities/`, and it left open whether
any other spelling should be read.

So a context laid out by area was told once for each area that the
directory held modules doctrine does not read, and passed every other
rule about its domain, having shown them nothing:

| In a context laid out by area | Doctrine, before this ADR |
|-------------------------------|---------------------------|
| An entity is a pydantic model | Objects to the directory, says nothing of the class |
| A repository returns `Any` | Objects to the directory, says nothing of the class |
| An oracle is bound to an entity kept in an area | Passes: the entity is not known to be one |

The only way to be checked was to give up the layout.

## Decision

**Under `domain/`, a directory named for a kind holds that kind, and
any other directory is an area.**

The kinds are the eight directory names julee already reads:
`models`, `values`, `repositories`, `services`, `handlers`, `oracles`,
`calculators` and `witnesses`.

Inside an area:

- A module the area holds directly is read as entities, as a module in
  `domain/models/` is.
- A directory named for a kind is read as that kind, exactly as it is
  directly under `domain/`.
- Any other directory is an area, read the same way.

What lies beneath a kind directory belongs to the kind, as it always
has. `domain/models/billing/` is more models, not an area, and a kind's
name further down decides nothing.

Nothing is declared. A directory is a kind's or an area by its name, so
there is no configuration and no second layout to select. Both orders
are read, and one context may use both.

An area is packaging inside a bounded context. It is not a bounded
context: discovery, the dependency rules and every rule that speaks of
"its context" still mean the package that holds `domain/`.

## Consequences

- The parser fills each family under `domain/` from the family's own
  directory and from each area. A class read in an area carries its
  path from `domain/`, which says which area it was read in.

- The resolver imports the same directories, so the rules that ask
  Python what a class is ask it of a class in an area too.

- An entity in an area is held to every entity rule, and counts among
  its context's entities when a rule asks what a port is bound to.

- A port in a kind directory inside an area is held to the port rules:
  what it is named, what it is bound to, what crosses it, and where it
  may be declared.

- A package whose only entities are in an area is found as a bounded
  context. An area holding Python is the entity layer being there.

- The rule that a package under `domain/` must be one doctrine reads is
  removed. Every directory under `domain/` is read now, so it had
  nothing left to object to.

- What that rule caught is still caught, by the rules about the classes
  themselves. `domain/repositorys/` is an area, since no kind is spelt
  that way; a protocol in it is read as an entity and objected to for
  not being one. `domain/entities/` is an area too, and its classes are
  entities, which is what the rule's author wanted read.

- `julee doctrine census` reports a class in an area as claimed at its
  location by the family that read it.

- No kit has an area, so the kits' families are what they were.

### What this does not reach

A module directly under `domain/`, such as `domain/errors.py`. It is in
no kind's directory and in no area, and no family reads it. The census
lists what it declares as unclaimed.

Which order a context should choose. An area above the kinds and an
area below them are both read, and this ADR prefers neither.

Entities and values kept together. A module in an area is read as
entities, so a value object there that is not an enum is counted as an
entity by the rules about what a port is bound to (ADR 018). A context
that wants its values apart gives the area a `values/` directory, or
keeps them in `domain/values/`.

`usecases/` and `dtos/`. Each is read with everything beneath it, so
either may already be divided by area, and nothing here changes them.

## Relationship to earlier ADRs

- **ADR 001** laid out `domain/` by kind. That layout is read as it was,
  and a context may now put an area above it.
- **ADR 002** is applied: a class in an area is still found by the
  directory it sits in, and what it is called is still a rule.
- **ADR 016** gave each driven port a directory under `domain/`. The
  same directory inside an area is that port's directory.
- **ADR 018** gave values a directory of their own, and the rule removed
  here learned to read it. The distinction stands, and an area keeps it
  by having a `values/` directory.
- **ADR 021** removed the names that hid a class from doctrine. This
  removes a directory that did.
