# ADR 018: A Value Object Has No Identity

## Status

Draft

## Date

2026-09-29

## Context

Doctrine reads every class under `domain/models/` as an entity. ADR 016
then defines all six driven ports by entity cardinality — a repository is
bound to one, a service to two or more, an oracle to none — so "entity"
is load-bearing: it decides which port a protocol is allowed to be.

Most classes under `domain/models/` are not entities.

Counting across the estate by what a repository is actually bound to:

| | classes | repository-bound |
|---|---|---|
| julee | 24 | 6 |
| c4 | 18 | 6 |
| hcd | 14 | 7 |
| ceap | 19 | 7 |
| polling | 5 | 0 |

`SystemContextDiagram` is assembled on demand and nothing stores one.
`PollingResult` is what a poll came back with. `JsonSchema` is a
schema. `QueryResult` is what a knowledge service answered. None of them
has an id, a lifecycle, or a repository, and each has at some point been
counted as a second aggregate a port was wrongly bound to.

### Four mechanisms, none of them the idea

The framework has needed this distinction four times and invented a
different proxy for it each time:

| mechanism | how it decides |
|---|---|
| `NOT_RECORDS` | a hand-written list of names |
| `_is_record` | whether it is a BaseModel or a dataclass |
| `VALUE_OBJECT_BASES` | whether it is built on `str` or `int` |
| `value_object_names` | whether a *base* is built on `str` or `int` |

Each was added where something broke. `NOT_RECORDS` had to name
`Acknowledgement` explicitly once it stopped being a BaseModel.
`value_object_names` was added because `ContentMultihash` extends
`NonEmptyText` extends `str`, and reading one base deep made ceap's
`DocumentRepository` look bound to two aggregates. Neither says what a
value object is; both approximate it from shape.

### The distinction itself

An entity has identity. It is the same thing tomorrow even if every
field changed, which is why a repository can keep it under an id and
hand it back: `Document` is the same document after its status changes.

A value object has none. Two with the same contents *are* the same one,
so there is nothing to keep and nothing to update — you replace it.
`Slug("a")` is not updated into `Slug("b")`; you have a different slug.

Everything doctrine cares about follows from that. No identity means no
repository, which means it cannot be what a port is bound to.

## Decision

**Value objects live in `domain/values/`. Doctrine reads that directory
as values and `domain/models/` as entities.**

The directory is the declaration, which is the convention this framework
already uses for every driven port: a protocol in `domain/oracles/` is an
oracle because of where it is. A value is a value for the same reason.

The four mechanisms above go, but not all at once and not all for the
same reason.

`value_object_names` is replaced immediately: it existed to guess from
base classes what the directory now states.

`NOT_RECORDS` and the record test behind `kernel_entity_names` go when
the kernel's own values move to `core/values/`. They answer the same
question as the directory — what may a port be bound to — for the one
codebase that has no bounded context to put a directory in.

`VALUE_OBJECT_BASES` stays, because it answers a different question.
It says a domain class may *be* a str or an int subclass, which is about
what shapes are allowed, not about what has identity. A value object
built on `str` is both things at once and each rule asks its own
question of it.

### Why not infer it

The obvious alternative was to compute it: a value is a domain class no
repository is bound to. It was rejected because it makes the
classification depend on how complete the repositories happen to be. A
new entity written before its repository would be read as a value, and
an entity read as a value is **silent** — a rule that stops counting an
aggregate simply objects to less. Adding a repository would silently
reclassify a class that had not changed.

Shape-based inference fails the same way from the other side. Any test
of the form "is it built on str" answers for `Slug` and not for
`JsonSchema`, which wraps a mapping and is no less a value.

### One directory, not two

`Slug` appears inside an entity; `QueryResult` is what a port hands
back. Both are values by the identity test, and they share a directory.

Splitting them was considered and rejected: doctrine uses only the one
fact — not an aggregate — so a split buys the rules nothing, and the
distinction would not hold. The day something stores a `QueryResult` on
an entity it becomes both, and would have to move. A classification that
flips while the code stands still is the kind this framework keeps
having to repair.

### The kernel

julee keeps its own domain classes in `core/entities/`, not in a
bounded context, so the same split applies as `core/values/`.
`kernel_entity_names()` feeds several port rules, and today it returns
mostly values.

## Consequences

- A new directory, `domain/values/`, added to the layer path constants.
  `READ_DOMAIN_PACKAGES` is derived from those, so doctrine stops
  objecting to it by construction.
- Roughly 37 classes move, and about 106 files name them. Almost all of
  that is one import line each, and mypy names every one.
- The port rules get the arity they were always asking for. An oracle
  returning a `JsonSchema` is bound to no entity, which is what an
  oracle is.
- `core/entities/` stops being three-quarters misnamed.
- A class in neither directory is still read as an entity, because
  `domain/models/` is where an entity goes and silence should mean the
  stricter reading.
