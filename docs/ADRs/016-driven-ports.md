# ADR 016: Naming the Driven Ports

## Status

Draft

## Date

2026-09-25

## Context

A use case depends on protocols and calls outward through them. In
hexagonal terms these are **driven ports**: the application drives them,
and an adapter in `infrastructure/` implements each one. Repositories,
services and handlers are all driven ports. So are two kinds this
framework has never named.

ADR 009 said the distinction between the first two is entity cardinality:

> A repository interface is semantically bound to ONE entity type.
> A service interface is semantically bound to TWO OR MORE entity types.
>
> This is the definitional difference. Everything else follows from it.

It claimed that rule was "simple enough to apply without debate" and that
it "covers all practical cases". Neither has held.

**It does not cover all practical cases.** A census across the five kits
and five downstream codebases found six protocols under `domain/` bound
to **no** entity at all. ADR 009 has no row for them, so each author
reached for whichever of the two available words felt least wrong. Three
chose `*Repository` and three chose `*Service`:

| Codebase | Protocol | Signature |
|---|---|---|
| ceap | `RemoteSchemaRepository` | `fetch(url: str) -> dict[str, Any]` |
| polling | `NewDataAnalyzer` | `identify_new_items(bytes \| None, bytes) -> list[str]` |
| onto-mapper-service | `HealthRepository` | `check_health() -> dict[str, list[str]]` |
| onto-mapper-service | `PromptService` | `get_prompt(name: str) -> str` |
| rba-accel-poc | `CredentialSignerService` | `sign_credential(...) -> dict[str, Any]` |
| rba-accel-poc | `DocumentTransferService` | `transfer_document(...) -> str` |

Four independent authors splitting evenly between two words that both fit
badly is not carelessness. It is a missing name.

**Cardinality was never the only axis.** ADR 003 introduced handler
protocols, which are distinguished by their *return type* —
`Acknowledgement` — and not by how many entities they touch. ADR 009 does
not mention handlers. The taxonomy has been running on two axes since
2025 without saying so.

**The second axis is already load-bearing in code.** `polling`'s only
Temporal workflow injects three driven ports into one use case inside
`@workflow.run`:

```python
use_case = PollDataUseCase(
    poller=WorkflowPollerServiceProxy(),   # proxied to an activity
    handler=self.get_handler(),            # called inline
    analyzer=self.get_analyzer(),          # called inline
)
```

The poller does HTTP, so it must be an activity: its answer can differ
between replays. The handler dispatches, which Temporal makes replayable
itself. The analyser compares two byte strings, so the same inputs give
the same answer and it is safe to run in workflow code. Somebody worked
all of that out port by port, correctly, with no vocabulary to record the
reasoning in.

## Decision

A driven port is classified on **two** axes.

1. **What it is bound to** — how many of its bounded context's entity
   types it names.
2. **What it costs to call** — whether a workflow must reach it through
   an activity, or may call it inline.

```
                          bound to
              ┌──────────┬────────────┬──────────┐
              │    0     │     1      │   2+     │
    ┌─────────┼──────────┼────────────┼──────────┤
    │ activity│  Oracle  │ Repository │ Service  │
    ├─────────┼──────────┴────────────┴──────────┤
    │ inline  │           Calculator             │
    └─────────┴──────────────────────────────────┘

    Handler: any arity, returns Acknowledgement, inline.
```

### Repository — one entity, activity

Bound to a single entity type. Its methods accept and return that entity
or primitives. Declares its entity through `RepositoryOf[Entity]`, which
`BaseRepository[Entity]` carries.

```python
class StoryRepository(BaseRepository[Story], Protocol):
    async def get(self, slug: str) -> Story | None: ...
    async def save(self, story: Story) -> None: ...
```

Lives in `domain/repositories/`. Named `{Entity}Repository`.

### Service — two or more entities, activity

Bound to two or more entity types, typically transforming between them.

```python
class KnowledgeService(Protocol):
    async def extract(self, document: Document) -> Knowledge: ...
```

Lives in `domain/services/`. Named `{Capability}Service`.

### Oracle — no entity, activity

Asks something the solution does not control, and gets an answer back in
that thing's own currency rather than ours: a remote endpoint, the
filesystem, a signing service, a liveness probe. It names no entity
because nothing it deals in has been modelled — which is honest, not
unfinished. Modelling foreign JSON as a domain entity would be a claim
the solution cannot keep.

```python
class SchemaOracle(Protocol):
    async def fetch(self, url: str) -> dict[str, Any]: ...
```

Lives in `domain/oracles/`. Named `{Capability}Oracle`. Implementations
live in `infrastructure/`, because an Oracle is where a bounded context
admits a runtime dependency on something outside the solution.

**An Oracle must be called from an activity.** It performs I/O; its
answer can differ between replays.

### Calculator — any arity, inline

Works out an answer from what it was handed. Same arguments, same answer,
every time.

```python
class NewDataCalculator(Protocol):
    async def identify_new_items(
        self, previous_data: bytes | None, new_data: bytes
    ) -> list[str]: ...
```

Lives in `domain/calculators/`. Named `{Capability}Calculator`.

**A Calculator may be called from workflow code**, which is the point of
naming it: without the name, the reflex is to wrap everything in an
activity and pay a round trip and a serialisation hop for a comparison of
two byte strings.

A Calculator is a port rather than a method on an entity when the answer
belongs to the **solution** rather than to the concept. A kit ships
`Story`; the solution that adopts it decides what "important" means. An
intrinsic rule with one right answer is a method on the entity. A rule
that varies by adopter, tenant or deployment is a Calculator, because the
entity cannot carry every adopter's version of it and should not import
what it would need to.

This is the seam a kit uses to require something from its adopter, which
is ADR 012's contribution contract running the other way.

### Handler — dispatch, inline

Accepts domain objects and decides what happens next, returning
`Acknowledgement` and nothing else (ADR 003). Classified by that return
type rather than by arity, because what a handler is *about* is the
handoff and not the payload.

Lives in `domain/services/`, in a file named `*_handler.py`. Named
`{Condition}Handler`. Callable inline: dispatching is a workflow-native
operation.

### Why the inline row is not divided by arity

On the activity row, arity decides real things: whether the framework can
generate a workflow proxy from the declared entity, what gets persisted,
and whether the protocol is doing the work of two. On the inline row none
of that applies. There is no I/O to manage and nothing to persist, so the
only thing worth saying about the port is that it is safe to replay.

A Calculator may therefore be bound to zero, one or several entities. The
census found only the zero case. Naming the axis rather than the arity
means the other two are already covered if they appear.

## Doctrine

What can be checked:

- A Repository is bound to exactly one entity, declared through
  `RepositoryOf[T]` (already enforced).
- A Service is bound to two or more.
- An Oracle is bound to none, and its implementations live in
  `infrastructure/`.
- A Handler's methods return `Acknowledgement` (already enforced).
- Each protocol is found by its directory, and its name must claim one of
  the five roles (ADR 002).

What cannot be checked, and is a claim the name makes: that a Calculator
is deterministic. Doctrine reads text; it cannot prove a function pure. A
Calculator that opens a socket is lying, and will be found out by a
non-determinism error on replay rather than by a failing test. This is
the same arrangement as everywhere else in doctrine — the name is a
claim, doctrine checks what it can, and the author is held to the rest.

## Consequences

### Positive

1. **The gap is closed.** Every driven port has a row, and no protocol is
   left choosing between two words that fit badly.
2. **The second axis becomes sayable.** A reader can tell from a port's
   name whether a workflow may call it inline, instead of deriving it
   case by case as polling's author had to.
3. **Handlers stop being an unmentioned exception.** They were already
   classified on the second axis; now the axis exists.
4. **A kit's extension seams have a name.** `NewDataAnalyzer` is a kit
   requiring something of its adopter, and that was previously invisible.

### Negative

1. **`domain/` gains two directories.** `models`, `repositories`,
   `services`, `oracles`, `calculators`. That is the cost of finding
   artifacts by their directory, which ADR 002 commits to.
2. **Renames across three codebases.** One protocol in ceap, one in
   polling, two in onto-mapper-service, two in rba-accel-poc. The kit
   ones are public names and need a version bump.
3. **"Oracle" leans read-shaped.** `DocumentTransferService` does
   something outward rather than asking something, and
   `DocumentTransferOracle` reads oddly. The category is "touches the
   world, so it must be an activity", which covers both directions —
   repositories have held `get` and `save` under one name since the
   beginning. The name is imperfect and the boundary is not.
4. **ADR 009's central claim is withdrawn.** Cardinality is one axis of
   two, not the definitional difference from which everything follows.

### Migration

| Was | Becomes |
|---|---|
| `ceap.RemoteSchemaRepository` | `SchemaOracle` |
| `polling.NewDataAnalyzer` | `NewDataCalculator` |
| `onto-mapper.HealthRepository` | `HealthOracle` |
| `onto-mapper.PromptService` | `PromptOracle` |
| `rba-accel-poc.CredentialSignerService` | `CredentialSignerOracle` |
| `rba-accel-poc.DocumentTransferService` | `DocumentTransferOracle` |

The two downstream codebases are not on this repository's release
schedule and adopt when they upgrade.

## References

- [ADR 002: Doctrine Test Architecture](./002-doctrine-test-architecture.md),
  for discovery by directory and naming by rule
- [ADR 003: Workflow Orchestration via Handler Services](./003-workflow-orchestration-handlers.md),
  which named the first port classified on the second axis
- [ADR 009: Repository vs Service Protocol Distinction](./009-repository-service-distinction.md),
  superseded by this
- [ADR 012: Separating the Framework from Domain Kits](./012-framework-and-kits.md),
  for the contribution contract a Calculator inverts
