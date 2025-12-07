Use Cases
=========

**Use cases orchestrate business logic.**

A use case coordinates :doc:`repositories` and :doc:`services`
to implement a domain workflow.
Use cases contain the application's business rules.

Use cases depend on :doc:`protocols`, not implementations.
They have no knowledge of databases, APIs, or frameworks.

:doc:`Applications </architecture/applications/index>` invoke use cases—whether through :doc:`APIs </architecture/applications/api>`, :doc:`CLIs </architecture/applications/cli>`, or :doc:`workers </architecture/applications/worker>`—but the use case itself remains unaware of how it was called.
