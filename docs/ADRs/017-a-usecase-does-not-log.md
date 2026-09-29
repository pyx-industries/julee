# ADR 017: A Use Case Does Not Log

## Status

Draft

## Date

2026-09-29

## Context

Use cases across this estate log. ceap's three largest hold 57 calls
between them, 39 in `initialize_system_data` alone. Every one of those
needs `import logging`, which is how a use case comes to import
something that is neither the domain nor the language it speaks.

Doctrine objects to the import (ADR 001, the dependency rule). The
objection is easy to satisfy and easy to satisfy wrongly: deleting the
calls makes the rule pass and throws away what the calls were for.
polling's use case went that way — it has no logging now, and nothing
was written down about where the information went.

So the question is not whether a use case may `import logging`. It is
where the information belongs once it may not.

### What the calls were actually doing

Reading them, they are two different things wearing one hat.

**Most are adapter events told from the wrong place.** "Content stored",
"document retrieved", "query executed" — each one describes what an
adapter just did, logged by the use case because the use case is who
called it. The adapter already knows; it is closer to the event and has
more of it.

**A few are decisions.** "No new data, stopping", "validation failed,
transforming" — these are the use case's own reasoning, and they are the
ones a reader of a production incident actually wants.

An adapter logging its own events loses nothing, because it knows them
better. But it loses the *thread*: twelve adapter calls in one run, and
nothing in the log says they belong together.

### The thread already exists

`ExecutionWitness` is a driven port with one method,
`get_execution_id()`. In a Temporal workflow it is backed by
`workflow.info().workflow_id`; elsewhere a UUID per instance. It was
added so a use case could name its own execution without knowing what
was running it (ADR 004).

That is the correlation identifier. Nothing else needs inventing.

## Decision

**A use case does not log. An adapter logs, and it logs with the
execution identifier.**

The identifier reaches the adapter through ambient context, not through
a widened signature. The composition root injects an `ExecutionWitness`
and whatever it injects is responsible for making the identifier
readable — a `contextvars.ContextVar` set at the start of the execution
is the mechanism this framework expects.

A use case that has something to say says it in its response. That is
what a response is for, and it is what polling already does: `Handoff`
and `handoff_info` report what became of the obligation to notify,
rather than logging it and returning nothing.

### Why ambient rather than a parameter

Passing the identifier explicitly was the alternative. It was rejected
because it puts an infrastructure concern in every port signature that
logs — `save(entity, run=run)` — and a driven port's signature is the
domain's sentence about what it needs. It does not need a log
correlation id; the thing on the other side does.

Ambient context has a second property that decided it: OpenTelemetry and
Temporal's interceptors both already propagate context this way. A
`ContextVar` set by the witness is readable by an OTel span processor and
by a Temporal interceptor without either knowing about julee.

### What this costs

Ambient state is invisible at the call site, which is the usual
objection to it, and it is a real one. The mitigation is that nothing in
the domain reads it: a use case neither sets nor gets the identifier, so
there is no hidden coupling to reason about inside the domain ring. Only
adapters read it, and an adapter is already the place where the
environment is allowed to show through.

An adapter that reads nothing logs without an identifier rather than
failing. A missing thread is a worse log, not a broken run.

## Consequences

- `logging` leaves every `usecases/` module. Doctrine's dependency rule
  enforces it, and it is now enforcing a decision rather than a
  preference.
- Adapters gain the logging the use cases were doing on their behalf,
  at the point where the event happens.
- A use case with something to report puts it in its response. A
  response that carries nothing a caller can act on is a use case that
  had nothing to say, which is also information.
- `ExecutionWitness` gains a documented second purpose. It was for a use
  case to name its execution; it is also how an adapter finds out which
  execution it is serving.
- polling's silent use case is retroactively correct, and now for a
  stated reason.
