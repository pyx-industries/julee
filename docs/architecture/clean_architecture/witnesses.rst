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

A witness is not deterministic. ``now()`` gives a different answer
every call, and always will.

It is still safe to call from workflow code,
because the runtime writes what it said into the execution history
the first time, and a replay is told the same thing.
Temporal calls this replay-stability, and it is a different promise
from a :doc:`calculator <calculators>`'s determinism.

**Never wrap a witness in an activity.**
Doing so is a defect rather than merely wasteful:
the value is already in the workflow history,
so the activity adds a round trip to fetch something the workflow holds.

Two Implementations, Always
---------------------------

A witness always has at least two implementations,
and that is intrinsic rather than incidental::

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
A witness cannot: outside a recording runtime
it gives a different answer every time, correctly.

What The Framework Ships
------------------------

Julee ships two, and every solution injects them:

- a clock, answering what time it is
- an execution identifier, answering which run this is

They are the reason the kind needed a name.
Both have existed since :doc:`ADR 004 </ADRs/004-execution-agnostic-use-cases>`,
both are called inline by every pipeline,
and until :doc:`ADR 016 </ADRs/016-driven-ports>` there was no sentence
anywhere saying what they were
or why wrapping one in an activity would be wrong.
