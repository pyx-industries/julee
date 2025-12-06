Solutions
=========

A **Julee Solution** is a software system built using the Julee framework—see :doc:`/architecture/framework` for what that means. This section covers how solutions should be structured.

.. toctree::
   :maxdepth: 1
   :caption: Topics

   composition
   pipelines
   modules
   batteries-included
   3rd-party


Organise Around Your Business Domain
------------------------------------

Remember: **a framework and a solution are different beasts.**
The framework provides vocabulary; your solution uses that vocabulary
to express your specific business domain.

Julee's codebase is organised around ``domain/``, ``infrastructure/``, ``repositories/``
because Julee is a framework—those *are* its domain concepts.

Your solution should be organised around *your* bounded contexts—
the distinct areas of your business that the solution serves.
This is what makes your architecture "speak" your business language.

::

    # Framework organisation (Julee itself)
    julee/
      domain/           # Framework vocabulary
      infrastructure/   # Framework implementations
      workflows/        # Framework patterns

    # Solution organisation (your application)
    invoice_processor/
      billing/          # Bounded context: billing domain
        domain/
          invoice.py
          payment.py
        use_cases/
          process_invoice.py
        infrastructure/
          invoice_repository.py
      compliance/       # Bounded context: compliance domain
        domain/
          audit_record.py
          policy.py
        use_cases/
          validate_invoice.py
      apps/             # Application entry points
        api/
        cli/
        worker/

Each bounded context contains its own domain models, use cases, and infrastructure—
using Julee's vocabulary (Repository, Service, UseCase patterns) to express
the specific concerns of that part of your business.


Bounded Contexts and Loose Coupling
-----------------------------------

Bounded contexts should be **loosely coupled**.
Each context owns its own:

- **Domain models**: ``billing/domain/invoice.py`` defines what an Invoice means *in the billing context*
- **Use cases**: ``billing/use_cases/process_invoice.py`` implements billing-specific business rules
- **Repositories**: ``billing/infrastructure/invoice_repository.py`` handles persistence for billing entities
- **Services**: External service integrations specific to that context

Contexts communicate through well-defined interfaces, not by reaching into each other's internals.

::

    # Good: contexts communicate through interfaces
    class BillingService(Protocol):
        async def get_invoice_total(self, invoice_id: str) -> Decimal: ...

    # compliance context uses the interface
    class ValidateInvoiceUseCase:
        def __init__(self, billing: BillingService):
            self.billing = billing

        async def execute(self, invoice_id: str):
            total = await self.billing.get_invoice_total(invoice_id)
            # validation logic...

    # Bad: compliance reaches into billing internals
    class ValidateInvoiceUseCase:
        def __init__(self, invoice_repo: InvoiceRepository):  # billing's repo!
            self.invoice_repo = invoice_repo  # tight coupling


Applications Adjacent to Contexts
---------------------------------

Application entry points (API, CLI, Worker, UI) sit *adjacent* to bounded contexts,
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

The ``apps/`` directory doesn't contain business logic—it contains the *glue*
that connects your bounded contexts to the outside world.


From Composition to Pipeline
----------------------------

Within each bounded context, the core building block is a **composition**—
a use case combined with the services and repositories it needs.

::

    Composition = Use Case + Services + Repositories

Compositions can be executed in two ways:

**Direct Execution**
    Run the composition immediately in an API endpoint or CLI command.
    Simple, synchronous, no audit trail.

**Pipeline Execution**
    Run the composition via Temporal as a workflow.
    Reliable, auditable, with supply chain provenance.

See :doc:`composition` for details. See :doc:`pipelines` for when and why to use pipeline execution.


Solution Architecture
---------------------

A typical Julee solution with bounded contexts looks like this:

::

    ┌─────────────────────────────────────────────────────────────────┐
    │                       Julee Solution                            │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │  Bounded Contexts (your business domain)                        │
    │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
    │  │    Billing      │ │   Compliance    │ │   Reporting     │   │
    │  │  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │   │
    │  │  │  domain/  │  │ │  │  domain/  │  │ │  │  domain/  │  │   │
    │  │  │ use_cases/│  │ │  │ use_cases/│  │ │  │ use_cases/│  │   │
    │  │  │  infra/   │  │ │  │  infra/   │  │ │  │  infra/   │  │   │
    │  │  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │   │
    │  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘   │
    │           │                   │                   │             │
    │           └───────────────────┼───────────────────┘             │
    │                               │                                 │
    │  Applications (entry points)  │                                 │
    │  ┌─────────┐ ┌─────────┐ ┌────┴────┐ ┌─────────┐               │
    │  │ Worker  │ │   API   │ │   CLI   │ │   UI    │               │
    │  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
    │                                                                 │
    │  Julee Framework (imported as dependency)                       │
    │  ┌─────────────────────────────────────────────────────────┐   │
    │  │ Batteries: CEAP workflows, MinIO repos, AI services     │   │
    │  │ Patterns: Repository, Service, UseCase protocols        │   │
    │  │ Utilities: Temporal integration, DI helpers             │   │
    │  └─────────────────────────────────────────────────────────┘   │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘


Next Steps
----------

- :doc:`composition` - How use cases combine with services
- :doc:`pipelines` - Reliable execution with supply chain provenance
- :doc:`modules` - Module types and integration patterns
- :doc:`batteries-included` - Ready-made components from the framework
- :doc:`/architecture/applications/index` - Application types (Worker, API, CLI, UI)
- :doc:`/architecture/clean_architecture/index` - Underlying layer structure
