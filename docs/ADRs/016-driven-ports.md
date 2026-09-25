# ADR 016: Naming the Driven Ports

## Status

Draft

## Date

2026-09-25

## Context

A use case depends on protocols and calls outward through them. In
hexagonal terms these are **driven ports**: the application drives them,
and an adapter in `infrastructure/` implements each one. Repositories,
services and handlers are all driven ports. So are three kinds this
framework has never named, two of which it ships itself.

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

**And being safe to call inline has more than one reason.** `ClockService`
and `ExecutionService` (`core/services/`) are bound to no entity and are
called inline — `integrations/temporal/clock.py` says its implementation
must only be used inside a workflow. Neither is deterministic:
`now()` gives a different answer every call. They are safe because the
runtime records what they said and replays the recorded value, which is a
third reason distinct from computing an answer and from dispatching.

They also show the cost of leaving a kind unnamed. These two are the
ports every julee solution injects, they have existed since ADR 004, and
until this ADR there was no sentence anywhere saying what they are or why
wrapping one in an activity would be wrong.

## Decision

A driven port is classified on **two** axes.

1. **What it is bound to** — how many of its bounded context's entity
   types it names.
2. **Whether it is replay-safe** — whether a workflow must reach it
   through an activity, or may call it inline.

```
                          bound to
              ┌──────────┬────────────┬──────────┐
              │    0     │     1      │   2+     │
    ┌─────────┼──────────┼────────────┼──────────┤
    │ activity│  Oracle  │ Repository │ Service  │
    ├─────────┼──────────┴────────────┴──────────┤
    │         │  Calculator   deterministic      │
    │ inline  │  Witness      replay-stable      │
    │         │  Handler      native dispatch    │
    └─────────┴──────────────────────────────────┘

    domain/  repositories/  services/  oracles/
             calculators/   witnesses/ handlers/
```

One directory per port, and every port found by its directory. Nothing
here is found by its name: a name is a claim doctrine checks, never the
mechanism that locates the thing.

Being reachable inline is one property with three reasons, and the
reasons are worth distinguishing because they are different promises:

| Port | Stable across | Testable |
|---|---|---|
| **Calculator** | *calls* — same arguments, same answer, anywhere | on its own |
| **Witness** | *replays* — same point in history, same answer | only inside a runtime that records |
| **Handler** | — dispatch is the engine's own operation | with a fake handler |

A Calculator is safe everywhere, including outside a workflow entirely. A
Witness is safe only because the runtime records what it said, which
makes it a framework-coupling seam where a Calculator is not.

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

### Witness — no entity, inline

Testifies to something about the execution itself: what time it is, which
run this is. Its answer is not computed from its arguments and is not the
same on every call — but the runtime writes it into the execution history
the first time, so a replay is told the same thing.

```python
class ClockWitness(Protocol):
    def now(self) -> datetime: ...
```

Lives in `domain/witnesses/`, or in `julee.core.witnesses` for the two
the framework ships. Named `{Subject}Witness`.

**A Witness may be called from workflow code, and must not be wrapped in
an activity.** Wrapping one defeats it: the point of
`TemporalClockWitness` is that `workflow.now()` is already recorded, and
an activity would add a round trip to obtain something the history
already holds.

A Witness always has at least two implementations and that is intrinsic
rather than incidental. `SystemClockWitness` returns `datetime.now(UTC)`,
which is not replay-stable and never will be; `TemporalClockWitness`
returns `workflow.now()`, which is. The port exists so a use case can ask
what time it is without knowing what is running it — ADR 004's purpose —
and it is therefore a framework-coupling seam in a way a Calculator is
not. That difference is why the two have separate names rather than one:
collapsing them would hide the only thing about a Witness that matters.

The framework ships two, and every solution uses them: a clock and an
execution identifier.

### Handler — dispatch, inline

Accepts domain objects and decides what happens next, returning
`Acknowledgement` and nothing else (ADR 003). Classified by that return
type rather than by arity, because what a handler is *about* is the
handoff and not the payload.

Lives in `domain/handlers/`, in a file named `*_handler.py`. Named
`{Condition}Handler`. Callable inline: dispatching is a workflow-native
operation.

Handlers shared `domain/services/` until this ADR, told apart by their
name. That made Handler the one port found the way #175 stopped finding
things, and it showed: `julee-hcd`'s services package held eleven
handlers and no services at all, so the directory's name described
nothing in it. A handler still sitting there is read as a handler, so
ADR 003's rules keep checking it, and objected to for where it is.

### Why the inline row is divided by reason, not by arity

On the activity row, arity decides real things: whether the framework can
generate a workflow proxy from the declared entity, what gets persisted,
and whether the protocol is doing the work of two. On the inline row none
of that applies. There is no I/O to manage and nothing to persist, so
arity says nothing useful and the division that matters is *why* the port
is safe to call there.

It matters because the three promises differ in what a reader may rely
on. A Calculator can be exercised with no harness at all. A Witness
cannot — outside a recording runtime it gives a different answer every
time, correctly. A Handler's inline safety belongs to the engine rather
than to the protocol.

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
- A Witness is bound to none, and is never given a workflow proxy —
  wrapping one in an activity is a defect a rule can see.
- Each protocol is found by its directory, and its name must claim one of
  the six roles (ADR 002).

What cannot be checked, and is a claim the name makes: that a Calculator
is deterministic, and that a Witness is replay-stable. Doctrine reads
text; it cannot prove a function pure, nor that an implementation reaches
for a recorded value rather than a live one. A Calculator that opens a
socket is lying, and so is a Witness whose workflow implementation calls
`datetime.now()`. Both are found out by a non-determinism error on replay
rather than by a failing test. This is the same arrangement as everywhere
else in doctrine — the name is a claim, doctrine checks what it can, and
the author is held to the rest.

## Consequences

### Positive

1. **The gap is closed.** Every driven port has a row, and no protocol is
   left choosing between two words that fit badly.
2. **The second axis becomes sayable.** A reader can tell from a port's
   name whether a workflow may call it inline, instead of deriving it
   case by case as polling's author had to.
3. **Handlers stop being an unmentioned exception.** They were already
   classified on the second axis; now the axis exists.
5. **The framework's own two ports are placed.** `ClockService` and
   `ExecutionService` fitted nothing until Witness existed, and they are
   the ports every solution uses.
4. **A kit's extension seams have a name.** `NewDataAnalyzer` is a kit
   requiring something of its adopter, and that was previously invisible.

### Negative

1. **`domain/` gains four directories.** `models`, `repositories`,
   `services`, `oracles`, `calculators`, `witnesses`, `handlers`. That is
   the cost of finding artifacts by their directory, which ADR 002
   commits to. Most bounded contexts will have three or four of them.
2. **Renames across three codebases, and two in the kernel.** One
   protocol in ceap, one in polling, two in onto-mapper-service, two in
   rba-accel-poc. `ClockService` and `ExecutionService` are julee's own
   public API and every solution injects them, so that rename is the
   widest-reaching change here and wants a deprecation alias rather than
   a straight cut.
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
| `julee.core.services.ClockService` | `ClockWitness` |
| `julee.core.services.ExecutionService` | `ExecutionWitness` |

Handlers move directory rather than name: `domain/services/*_handler.py`
becomes `domain/handlers/*_handler.py`. Eleven files in `julee-hcd`, one
in `julee-polling`. Doctrine reads them either way and objects while they
are in the old place, so the move can happen when convenient rather than
in lockstep with the framework.

The two downstream codebases are not on this repository's release
schedule and adopt when they upgrade.

`ClockService` and `ExecutionService` are injected by every solution
built on julee. Rename with an alias kept for a release, not with a cut.

`julee.core.services/` becomes `julee.core.witnesses/`, which leaves the
kernel with no `services/` package — correct, since neither of the two
was ever a service under ADR 009's own rule.

## References

- [ADR 002: Doctrine Test Architecture](./002-doctrine-test-architecture.md),
  for discovery by directory and naming by rule
- [ADR 003: Workflow Orchestration via Handler Services](./003-workflow-orchestration-handlers.md),
  which named the first port classified on the second axis
- [ADR 009: Repository vs Service Protocol Distinction](./009-repository-service-distinction.md),
  superseded by this
- [ADR 004: Execution-Agnostic Use Cases](./004-execution-agnostic-use-cases.md),
  which introduced the two Witnesses without a word for them
- [ADR 012: Separating the Framework from Domain Kits](./012-framework-and-kits.md),
  for the contribution contract a Calculator inverts
