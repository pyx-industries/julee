Handlers
========

**Handlers decide what happens next.**

A :doc:`use case <use_cases>` does its job, recognises a domain condition,
and hands off. It does not compute the next action itself.

::

    class OrphanStoryHandler(Protocol):
        async def handle(self, story: Story) -> Acknowledgement: ...

This is the "green-dotted-egg" principle of :doc:`ADR 003
</ADRs/003-workflow-orchestration-handlers>`.
The use case recognises that a story has no epic
and hands the story to a handler,
without knowing whether that handler queues work,
sends a notification, or dispatches a pipeline.

Handlers accept domain objects, not requests.
What a handler does internally is the handler's business.

Handlers live in ``domain/handlers/``,
in a file named ``*_handler.py``.

They shared ``domain/services/`` until ADR 016,
told apart by their name rather than their directory—
the one port found the way everything else had stopped being found.
A handler still sitting there is read as a handler,
so its rules keep applying, and doctrine objects to where it is.

Always Acknowledgement
----------------------

A handler method returns ``Acknowledgement`` and nothing else—
wilco, unable, or roger.
That gives the use case a uniform signal about whether the handoff
was accepted, without it knowing what the handler does.

An acknowledgement says whether the handoff was accepted.
It does not carry a result,
and widening it to carry one would make every handler's answer
mean two things.

This is why a handler is classified by its return type
rather than by how many :doc:`entities` it touches.
What a handler is *about* is the handoff, not the payload.

If You Need A Value Back
------------------------

Wanting a value back is the signal that the handler shape is wrong,
not that ``Acknowledgement`` is too narrow.
Which port you actually want depends on what it deals in:

- two or more of this context's entities — a :doc:`service <services>`
- exactly one — a :doc:`repository <repositories>`
- none, and it must ask something outside the solution — an :doc:`oracle <oracles>`
- none, and the answer follows from what you handed it — a :doc:`calculator <calculators>`
- none, and it reports on the execution — a :doc:`witness <witnesses>`

Handlers Run Inline
-------------------

A :doc:`pipeline </architecture/solutions/pipelines>` calls a handler
directly, without wrapping it in an activity.
Dispatch is an operation Temporal provides itself—
starting a child workflow, sending a signal—
and the engine makes those replayable.

The safety belongs to the engine rather than to the protocol,
which is what separates a handler from a :doc:`calculator <calculators>`
(safe because it is deterministic)
and from a :doc:`witness <witnesses>` (safe because the runtime records it).

Why Cross-Context Handoff Needs This
------------------------------------

A reusable kit cannot know what comes after it.
When the polling kit detects new data,
it should trigger downstream processing—
but it cannot know whether that is document capture,
data transformation, or something else entirely.

The handler protocol lets the kit say "something happens here"
and lets the solution's composition root say what.
