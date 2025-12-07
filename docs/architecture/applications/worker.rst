Workers
=======

A worker is a Temporal worker process that polls for work and executes pipeline activities. Workers are the application type for long-running, reliable processes with audit trails.

Workers connect to a Temporal server and poll a task queue. When a pipeline is triggered, Temporal schedules activities which the worker executes. Each activity represents a use case step—fetching documents, calling AI services, storing results. Temporal records the execution history, enabling replay and recovery.

Temporal automatically retries failed activities with configurable backoff. Multiple worker instances can run concurrently; Temporal distributes work across them. Workflow code must be deterministic for replay; side effects belong in activities.

Temporal UI provides visibility into running and completed workflows, activity execution history, retry attempts, errors, and input/output data.
