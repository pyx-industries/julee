Dependency Injection
====================

**Dependency injection wires implementations to protocols.**

:doc:`Use cases <use_cases>` depend on :doc:`protocols`, not implementations.
The DI container provides concrete implementations
of the six :doc:`driven ports <protocols>` that satisfy those protocols.

Applications depend on the DI container.
The container provides the ports;
applications wire use cases using those dependencies.
This makes implementations swappable without changing business logic.

A :doc:`pipeline </architecture/solutions/pipelines>` wires the same use case
differently: ports that do I/O are replaced with proxies
that route through Temporal activities,
while :doc:`calculators`, :doc:`witnesses` and :doc:`handlers`
are injected as they are.
The use case cannot tell the difference, which is the point.
