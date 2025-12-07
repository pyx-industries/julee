Clean Architecture
==================

Both the :doc:`Julee Framework </architecture/framework>`
and :doc:`Julee Solutions </architecture/solutions/index>`
organize their code using Robert C Martin's "Clean Architecture" principles.
This document will just focus on Julee's interpretation and implementation.

Clean Architcture is strict about how the dependencies in code are organised.
There are other similar schemes, such as Alistair Cockbourn's "Hexagonal Architecture"
(a.k.a "ports and adapters"), which share the same core goals
of **dependency inversion** and **separation of concerns**. They both:

* Place business logic at the center, isolated from external concerns
* Make external dependencies (databases, UI, external services) plug into the core rather than vice versa
* Use dependency inversion to point dependencies inward
* Aim for testability and flexibility in swapping implementations

For comparison, Hexagonal architecture uses a simpler two-part model
(inside/outside) focused on ports and adapters,
without prescribing how to structure the business logic inside.
Clean Architecture defines multiple concentric layers
with specific responsibilities for each.
Essentially, Clean Architecture is more prescriptive
about the internal organization while Hexagonal Architecture
is more minimal and focused on the boundary between core and infrastructure.
It is essentially a 3 layer, rather than a 2 layer system.

.. uml:: ../diagrams/clean_architecture_layers.puml


Demonstration
-------------

One of the :doc:`contrib modules </architecture/solutions/contrib>`
is a "Capture, Extract, Assembly, Publish" workflow (CEAP).
This is a general purpose AI heuristic
which is useful in a lot of circumstances.
Rather than talking about the clean architecture in theory,
we will walk through a part of this by way of an example.

This is an automated process with no user interaction,
so it is done by an application called a :doc:`Worker </architecture/applications/worker>`.
We will specifically look at the :doc:`pipeline </architecture/solutions/pipelines>`
called :py:class:`~julee.domain.use_cases.ExtractAssembleDataUseCase`.
This is the most complicated and interesting part of CEAP.

... uml:: ../diagrams/ceap_workflow_sequence.puml

A usecase is usually specific to a business domain,
CEAP is unusual because it's a generic, reusable pattern.
That's why it's part of the framework,
so you can reuse it without having to reinvent the wheel.

This usecase is understandable and testable,
but it leaves a lot to the imagination.
What is a KnowledgeService? a DocumentRepository?
a AssemblyRepository, AssemblySpecificationRepository,
KnowledgeServiceQueryRepository, or a KnowledgeServiceConfigRepository?
How do they work? Those questions are answered separately.

:doc:`Repositories <repositories>` store and access data.
As long as the usecase can use them,
it shouldn't have to care about how they work.
So "what is the repository" is first defined in the abstract,
using a python :doc:`Protocol <protocols>` specification,
which is part of the domain model.

Second, "how do they work" is an infrastructure concern.
There is code that implements the protocol using technology.
Actually, we have more than one implementation of each -
MinIO implementations for production, memory implementations for testing.
The memory implementations are volatile and unsuitable for production,
but useful as testing doubles in unit tests
that run fast and in parallel without external dependencies.

So, each usecase defines a deterministic business process,
but a lot of the heavy lifting is being done
by the :doc:`entity <entities>` classes in the domain model.
The repository protocols are strongly typed -
they proscribe that inputs and outputs are either
domain model classes or simple primitives.

Entities are more than dumb data containers.
They are rich objects in their own right,
with derivative methods that validate and calculate properties.
They have both data and behavior,
they encapsulate some of the business rules.

In general, these domain model abstractions
(entities, repository and service protocols)
serve to protect the usecase from the vagaries of the external systems.
This also makes the implementations "swappable",
anything that conforms to the protocol will do.
This is how it is possible for the :doc:`Dependency Injection <dependency_injection>`
container to do its job - it provides the :doc:`application <applications>`
with repositories and services that satisfy the protocols,
and henceforth the usecases just use them.


.. toctree::
   :maxdepth: 1
   :caption: Details

   entities
   use_cases
   repositories
   services
   protocols
   dependency_injection
   applications

