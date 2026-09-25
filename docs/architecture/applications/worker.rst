Workers
=======

A worker is a Temporal worker process that polls for work and executes :doc:`pipeline </architecture/solutions/pipelines>` activities. Workers are the application type for long-running, reliable processes with audit trails.

Workers connect to a Temporal server and poll a task queue. When a :doc:`pipeline </architecture/solutions/pipelines>` is triggered, Temporal schedules activities which the worker executes. Each activity is a call to one of the :doc:`driven ports </architecture/clean_architecture/protocols>` that does I/O—fetching documents through a :doc:`repository </architecture/clean_architecture/repositories>`, asking an AI provider through an :doc:`oracle </architecture/clean_architecture/oracles>`, storing results. Temporal records the execution history, enabling replay and recovery.

Not every port becomes an activity. A :doc:`calculator </architecture/clean_architecture/calculators>`, a :doc:`witness </architecture/clean_architecture/witnesses>` and a :doc:`handler </architecture/clean_architecture/handlers>` are called inline in workflow code, because each is replay-safe for its own reason. :doc:`Pipelines </architecture/solutions/pipelines>` sets out which is which.

Temporal automatically retries failed activities with configurable backoff. Multiple worker instances can run concurrently; Temporal distributes work across them. Workflow code must be deterministic for replay; side effects belong in activities.

Temporal UI provides visibility into running and completed workflows, activity execution history, retry attempts, errors, and input/output data.

:doc:`Pipelines </architecture/solutions/pipelines>` can be triggered by :doc:`APIs <api>` for user-initiated operations, by :doc:`CLIs <cli>` for administrative or batch tasks, or by scheduled triggers within Temporal itself.
