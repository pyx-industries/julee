Witnesses
=========

**Witnesses testify to something about the execution itself.**

What time is it? Which run is this?
A witness answers a question about the running execution
rather than about your domain.

::

    class ClockWitness(Protocol):
        def now(self) -> datetime: ...

A witness names no :doc:`entity <entities>`, like an :doc:`oracle <oracles>`,
but the resemblance stops there. An oracle asks the outside world;
a witness asks the runtime it is running in.

Witnesses Run Inline
--------------------

A witness observes execution context rather than calculating from domain
arguments. Its answer need not change on every call: an execution identifier
is stable for the execution, and a test clock can return a fixed time.

A workflow-backed implementation can be called inline from workflow code.
``TemporalClockWitness`` reads ``workflow.now()`` and
``TemporalExecutionWitness`` reads ``workflow.info().workflow_id``;
Temporal supplies replay-stable values. The protocol alone does not provide
that guarantee. Replay-stability differs from a
:doc:`calculator <calculators>`'s calculation from its inputs.

**Never wrap a witness in an activity.**
The workflow-backed implementations read context the workflow runtime already
holds. A system-clock implementation belongs outside workflow code; wrapping
it in an activity changes what time is being observed rather than making it
a workflow clock.

Choose The Execution Implementation
-----------------------------------

Julee provides different clock implementations for different execution contexts::

    class SystemClockWitness:
        def now(self) -> datetime:
            return datetime.now(UTC)          # never replay-stable

    class TemporalClockWitness:
        def now(self) -> datetime:
            return workflow.now()             # replay-stable

The first is correct outside a workflow and wrong inside one.
The second is the reverse.
The protocol exists so a :doc:`use case <use_cases>` can ask the time
without knowing what is running it,
which is the purpose :doc:`ADR 004 </ADRs/004-execution-agnostic-use-cases>`
was written for.

That makes a witness a framework-coupling seam
in a way a :doc:`calculator <calculators>` is not.
A calculator can be exercised with no harness at all.
A witness needs an execution implementation or a test double. Outside a
workflow, ``SystemClockWitness`` reads wall-clock time and
``DefaultExecutionWitness`` creates an identifier per instance, unless a fixed
one is supplied. Neither supplies Temporal's replay guarantees.

What The Framework Ships
------------------------

Julee ships two witness protocols; use cases inject them when needed:

- a clock, answering what time it is
- an execution identifier, answering which run this is

They are the reason the kind needed a name.
Both have existed since :doc:`ADR 004 </ADRs/004-execution-agnostic-use-cases>`,
both are called inline by every pipeline,
and until :doc:`ADR 016 </ADRs/016-driven-ports>` there was no sentence
anywhere saying what they were
or why wrapping one in an activity would be wrong.
