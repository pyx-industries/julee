"""Clean Architecture foundation for julee solutions.

Both the Julee Framework and Julee Solutions organize their code using
Robert C Martin's "Clean Architecture" principles. This module provides
the shared infrastructure, repository protocols, and base classes that
embody these principles.

Clean Architecture vs Hexagonal Architecture
--------------------------------------------
Clean Architecture is strict about how dependencies in code are organised.
There are other similar schemes, such as Alistair Cockburn's "Hexagonal
Architecture" (a.k.a "ports and adapters"), which share the same core goals
of **dependency inversion** and **separation of concerns**. They both:

* Place business logic at the center, isolated from external concerns
* Make external dependencies (databases, UI, external services) plug into
  the core rather than vice versa
* Use dependency inversion to point dependencies inward
* Aim for testability and flexibility in swapping implementations

For comparison, Hexagonal architecture uses a simpler two-part model
(inside/outside) focused on ports and adapters, without prescribing how
to structure the business logic inside. Clean Architecture defines multiple
concentric layers with specific responsibilities for each. Essentially,
Clean Architecture is more prescriptive about the internal organization
while Hexagonal Architecture is more minimal and focused on the boundary
between core and infrastructure. It is essentially a 3 layer, rather than
a 2 layer system.

Protection Through Abstraction
------------------------------
The domain model abstractions (entities, repository and service protocols)
serve to protect the use case from the vagaries of external systems. This
also makes implementations "swappable" - anything that conforms to the
protocol will do. This is how the Dependency Injection container does its
job: it provides the application with repositories and services that satisfy
the protocols, and henceforth the use cases just use them.

The repository protocols are strongly typed - they prescribe that inputs
and outputs are either domain model classes or simple primitives. No
framework types leak into the domain.

Import directly from submodules::

    from julee.core.utils import normalize_name, slugify
    from julee.core.entities.bounded_context import BoundedContext
    from julee.core.repositories.bounded_context import BoundedContextRepository
"""
