Use Cases
=========

**Use cases orchestrate business logic.**

A use case coordinates :doc:`repositories` and :doc:`services`
to implement a domain workflow.
Use cases contain the application's business rules.

Use cases depend on :doc:`protocols`, not implementations.
They have no knowledge of databases, APIs, or frameworks.

Shared Application Helpers
--------------------------

A helper that looks up data through ports and assembles a response performs
application orchestration. A pure calculation over supplied domain values
belongs in the domain. Keep that distinction when sharing logic.

Current doctrine rejects imports from another module under a bounded
context's ``usecases/`` package, including an adopted kit's package.
The rule checks import paths; it does not distinguish helper functions from
executable use-case entry points. The :doc:`handler <handlers>` convention
supports handing off a domain condition, rather than obtaining a shared
helper's result. This restriction does not make an I/O-performing helper a
pure domain calculation; naming or relocating it cannot change its role.

Execution
---------

:doc:`Applications </architecture/applications/index>` invoke use cases through
:doc:`APIs </architecture/applications/api>`,
:doc:`CLIs </architecture/applications/cli>` or
:doc:`workers </architecture/applications/worker>`.
The use case remains unaware of how it was called.

A :doc:`pipeline </architecture/solutions/pipelines>` supplies durable workflow
execution when its dependencies are wired for replay: I/O uses activities,
time and identity use workflow-backed :doc:`witnesses`, and
:doc:`handlers` use replayable workflow operations. Injecting a protocol
alone does not establish those guarantees. Activity retries follow the
configured policy; effects that may repeat need an idempotency strategy.
