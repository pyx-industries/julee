Dependency Injection
====================

**Dependency injection wires implementations to protocols.**

:doc:`Use cases <use_cases>` depend on :doc:`protocols`, not implementations.
The DI container provides concrete implementations
(:doc:`repositories` and :doc:`services`) that satisfy those protocols.

Applications depend on the DI container.
The container provides repositories and services;
applications wire use cases using those dependencies.
This makes implementations swappable without changing business logic.
