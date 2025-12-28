Solutions
=========

A **Julee Solution** is a software system
built on the :py:mod:`Julee framework <julee>`.
The framework provides the vocabulary and patterns
for orchestrating a digital product supply chains.


Organise Around Your Business Domain
------------------------------------

The Julee framework codebase is organised around software architecture concepts,
because Julee is a framework; those *are* its domain concepts.

A Julee solution should be organised around *your* bounded contexts —
the distinct areas of your business that the solution serves.
These are your :doc:`accelerators <accelerators>`.
This is what makes your architecture "speak" your business language.

::

    # Framework organisation (Julee itself)
    julee/
      domain/           # Framework vocabulary
      infrastructure/   # Framework implementations
      workflows/        # Framework patterns

    # Solution organisation (your application)
    your_business/      # Bounded contexts of your business
      billing/
        domain/
          invoice.py
          payment.py
        use_cases/
          process_invoice.py
        infrastructure/
          invoice_repository.py
      compliance/
        domain/
          audit_record.py
          policy.py
        use_cases/
          validate_invoice.py
      apps/             # Application entry points
        api/
        cli/
        worker/

Each accelerator contains its own domain models, :py:class:`use cases <julee.core.entities.use_case.UseCase>`, and infrastructure —
using Julee's vocabulary (:py:class:`Repository <julee.core.entities.repository_protocol.RepositoryProtocol>`, :py:class:`Service <julee.core.entities.service_protocol.ServiceProtocol>`, UseCase patterns) to express
the specific concerns of that part of your business.
Use cases become :doc:`pipelines <pipelines>` when run with Temporal for durability and audit trails.


Applications Adjacent to Contexts
---------------------------------

:doc:`Application </architecture/applications/index>` entry points (API, CLI, Worker, UI) sit *adjacent* to bounded contexts,
not above or below them. They wire together the contexts and expose them to the outside world.

::

    invoice_processor/
      billing/              # Bounded context
      compliance/           # Bounded context
      shared/               # Shared kernel (if needed)
      apps/
        api/
          routers/
            billing.py      # Exposes billing context via REST
            compliance.py   # Exposes compliance context via REST
          dependencies.py   # DI wiring
        worker/
          workflows/
            invoice_workflow.py  # Orchestrates across contexts
        cli/
          commands/
            billing.py
            compliance.py

The ``apps/`` directory doesn't contain business logic,
it provides a way for it to interact with the outside world.


Solution Architecture
---------------------

A typical Julee solution with bounded contexts looks like this:

.. uml:: ../diagrams/solution_architecture.puml

There is at least one application (CLI, API, UI, Worker)
which contains configuration and depends on the bounded contexts.
Typically this would include an API and a Worker (at least).

There are various ways that the solution can have dependencies on the framework.
The solution might:

- import some :doc:`contrib <contrib>` :doc:`pipelines <pipelines>`, to avoid reinventing the wheel
- have new infrastructure implementation of an imported interfaces

The solution might also have dependencies on a :doc:`3rd-party component <3rd-party>`, e.g:

- importing a bounded context and using it's parts
- importing a service and running it locally, as part of the solution
- operating a gateway service (runtime dependency on a 3rd party service)

As well as using their own bespoke bounded context(s).

.. toctree::
   :maxdepth: 1
   :hidden:

   accelerators
   pipelines
   contrib
   modules
   3rd-party
