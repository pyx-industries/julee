# ADR 015: Kits Claim, Solutions Decide

## Status

Draft

## Date

2026-09-24

## Context

Two bounded contexts do not share meaning. That is what makes them
bounded. But a solution's documentation is poorer if nobody says that a
`Story` in one and a `UseCase` in another are the same event told from
two sides, or that the people on a C4 diagram are the personas the
human-centred design work describes.

ADR 007 answered this with a decorator on the entity class, a `RelationType`
enum of ten values, and a registry populated at import time. That design
was never on master — it existed only on `archive/docs_architecture_domain`
— and porting the domain into kits showed why it should not come back.

**It made one kit depend on another.** `Integration` declared a relation
to `julee.supply_chain.entities.accelerator.Accelerator`: public code
naming a class in a private repository. It survived because a decorator
argument is a string nobody resolves.

**Nothing was ever checked.** Of the ten relations declared, two named
classes that do not exist — `julee.core.entities.application.Application`
and `julee.core.entities.use_case.UseCase`. They had been dangling for as
long as the decorators had.

**Seven of the ten restated fields.** An epic containing stories is
`Epic.story_refs`. A story belonging to an app is `Story.app_slug`. Those
are the shape of one kit's own model, readable from it, and copying them
into a decorator created a second copy to keep in step.

**The registry was populated by import.** What the documentation knew
depended on which modules had been imported, and in what order. Nothing
static could see it.

So one relation of the ten was worth declaring, and the mechanism for
declaring it was the problem.

## Decision

A kit publishes **claims** about how its terms line up with other
people's. A solution decides what it holds true. Nothing merges by
itself.

### A claim

`Claim`, in `julee.core.entities.claim`, with a `ClaimKind` of five
values: `is_a`, `projects`, `part_of`, `contains`, `references`. The
archived enum had ten; the other five were declared and never used once.
The vocabulary grows when something needs it to.

Both ends are dotted paths to classes. Names, not imports.

A `note` says why the claim is made. It is what makes a claim
documentation rather than configuration: a reader learning that two
classes are related wants to know why, and that is the part they cannot
work out for themselves.

### Where claims live

A kit ships `semantics.toml` as package data:

```toml
[[claim]]
id = "story-projects-usecase"
source = "julee_hcd.domain.models.story.Story"
kind = "projects"
target = "julee.core.entities.use_case.UseCase"
note = """
A story is what somebody wants, in their words. A use case is what the
system does about it. The story projects the use case: same event, told
from the outside.
"""
```

A solution keeps `semantics/` beside `apps/`:

```toml
[adopt]
hcd = "all"
c4 = ["person-is-a-persona"]
supply-chain = "none"

[[claim]]
id = "segment-is-a-persona"
source = "acme.domain.models.CustomerSegment"
kind = "is_a"
target = "julee_hcd.domain.models.persona.Persona"
note = "Our segments are personas by another name."
```

`load_semantics(solution_root, kits)` resolves the two.

### Silence is not consent

A solution that says nothing holds nothing. Adopting a kit is not
adopting its opinions about its neighbours, and a kit is not entitled to
act on its own claim.

This applies to behaviour as well as documentation. `julee-viewpoints`
draws a C4 person with the name and description of the matching HCD
persona **only** when the solution has accepted the claim that they are
the same person. A solution that has declined it, or has said nothing,
gets the bare slug.

### Doctrine resolves what the decorators never did

- A kit may claim only about classes it owns. Claiming about two other
  kits' classes is speaking for people who did not ask.
- A kit's claims must name classes its own package really has.
- A far end must resolve when its package is installed. One naming a kit
  nobody has installed cannot be checked, and allowing that is how a
  claim stays useful to a solution that later adopts both.
- A solution's claims must resolve at both ends.
- One pair of classes may not be claimed two ways. Two kits can disagree;
  settling it is the solution's job, done by declining one.
- A claim should say why.

### What is not a claim

Relationships inside one bounded context. They are already fields, and
introspection can read them. `semantics.toml` is for what crosses a
boundary, where no field can reach.

## Consequences

### Positive

- A kit cannot create a dependency by claiming. `semantics.toml` is read
  as package data, so resolving every adopted kit's claims imports no kit
  code at all — not even transitively.
- Claims are checked. The two dangling references in the archived set
  could not be written today.
- Provenance is visible. A reader can see what a kit offered beside what
  the solution took.
- Conflicts surface. Two kits claiming the same pair differently is an
  error the solution must settle, rather than something import order
  decides.
- Claims render. `semantics-index` and `kit-claims` project them into the
  documentation, which is where the `note` was always aimed.

### Negative

- A solution must opt in. Accepting a kit's claims is a line of TOML that
  did not exist before, and a solution upgrading from the decorator world
  gets nothing until it writes one. That is the intended cost.
- `adopt = "all"` means a kit upgrade can add claims a solution did not
  review. The same class of thing as an unpinned dependency, and the
  reason `load_semantics` reports what it resolved.
- Two places to look. A kit's claims and a solution's decision are
  separate files, deliberately.

### Neutral

- Dotted paths are strings, so an IDE will not rename through them.
  Doctrine catches what a rename breaks, which the decorators did not.

## Alternatives Considered

### Relations on the kit manifest

`Kit(relations=(...))` was the first proposal in this round. Rejected: a
manifest naming another kit's entities is the same coupling as the
decorator, moved from an argument into a tuple.

### A kit shipping a default map the solution imports

Rejected: a solution would inherit relations it never declared, which is
the consent problem again with an extra step. A kit publishes what it
claims; the solution reads it and decides.

### Keeping the decorator, checking it with doctrine

Rejected: the registry is still populated at import time, so doctrine
would only see what had been imported. The problem is the mechanism, not
the absence of rules over it.

### Why ADR 007 rejected an external file, and why that was wrong

ADR 007 considered a YAML mapping file and rejected it on three grounds.
Each is worth answering, because the design here is that alternative.

> Separates declaration from entity

Deliberately, and this is the point rather than a cost. An entity
declaring a relation to another kit's entity is an entity that knows
about another kit. The declaration belongs where it can be made without
creating that dependency.

> Easy to get out of sync

The opposite happened. The decorators went out of sync — two of ten named
classes that do not exist — precisely because nothing resolved them. Data
in a file can be checked, and is.

> Not discoverable via introspection

It is discoverable; that is what `load_semantics` does. What it is not is
discoverable *by importing*, which was the actual requirement behind the
objection, and which turned out to be the flaw.

## References

- [ADR 007: Semantic Relations Decorator Pattern](./007-semantic-relations.md),
  superseded by this
- [ADR 012: Separating the Framework from Domain Kits](./012-framework-and-kits.md)
- [SKOS Simple Knowledge Organization System](https://www.w3.org/2004/02/skos/),
  where the vocabulary comes from
