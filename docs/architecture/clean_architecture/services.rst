Services
========

**Services transform between entities.**

A service is bound to two or more :doc:`entities`
— its bounded context's, or the kernel's —
and typically turns one into another::

    class KnowledgeService(Protocol):
        async def extract(self, document: Document) -> Knowledge: ...

That is what separates a service from a :doc:`repository <repositories>`,
which is bound to exactly one entity and stores it.
Counting entities is the first of the two questions
:doc:`protocols` asks of every driven port.

Services are defined as :doc:`protocols`;
the :doc:`DI container <dependency_injection>` provides implementations.

A service does I/O, so a :doc:`pipeline </architecture/solutions/pipelines>`
reaches it through a Temporal activity rather than calling it inline.

Not An External Shim
--------------------

A protocol that delegates to an external actor in the digital supply chain
is usually not a service.
If it deals in a remote system's currency rather than your entities,
it is an :doc:`oracle <oracles>`.
``*Service`` was the closest available word before oracles were named,
which is why several protocols across the kits still wear it wrongly.
