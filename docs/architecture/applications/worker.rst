Workers
=======

A worker is a Temporal worker process that polls for work and executes :doc:`pipeline </architecture/solutions/pipelines>` activities. Workers are the application type for long-running, reliable processes with audit trails.

Workers connect to a Temporal server and poll a task queue. When a :doc:`pipeline </architecture/solutions/pipelines>` is triggered, Temporal schedules activities which the worker executes. Each activity represents a :py:class:`use case <julee.core.entities.use_case.UseCase>` step—fetching documents, calling AI :py:class:`services <julee.core.entities.service_protocol.ServiceProtocol>`, storing results. Temporal records the execution history, enabling replay and recovery.

Temporal automatically retries failed activities with configurable backoff. Multiple worker instances can run concurrently; Temporal distributes work across them. Workflow code must be deterministic for replay; side effects belong in activities.

Temporal UI provides visibility into running and completed workflows, activity execution history, retry attempts, errors, and input/output data.

:doc:`Pipelines </architecture/solutions/pipelines>` can be triggered by :doc:`APIs <api>` for user-initiated operations, by :doc:`CLIs <cli>` for administrative or batch tasks, or by scheduled triggers within Temporal itself.
