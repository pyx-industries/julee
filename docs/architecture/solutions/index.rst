Solutions
=========

A **Julee Solution** is a software system built using the Julee framework to solve specific business problems.

Solutions compose use cases with services to create value. They may run compositions directly (for simple operations) or as pipelines (for reliable, auditable execution).

.. toctree::
   :maxdepth: 1
   :caption: Topics

   composition
   pipelines
   modules
   batteries-included
   3rd-party

What is a Julee Solution?
-------------------------

A Julee Solution is:

- A software system built to meet specific business requirements
- Composed of one or more **applications** (Worker, API, CLI, UI)
- Built using the Julee framework's patterns and components
- Extended with domain-specific code for your business logic

Solutions combine:

**Domain-Specific Code**
    Your business models, use cases, and rules. This is what makes your solution unique.

**Framework Components**
    Julee's infrastructure - repository patterns, service protocols, DI container, Temporal integration.

**Modules**
    Reusable functionality from batteries-included modules (like CEAP) or third-party plugins.

From Composition to Pipeline
----------------------------

The core building block is a **composition** - a use case combined with the services and repositories it needs.

::

    Composition = Use Case + Services + Repositories

Compositions can be executed in two ways:

**Direct Execution**
    Run the composition immediately in an API endpoint or CLI command. Simple, synchronous, no audit trail.

**Pipeline Execution**
    Run the composition via Temporal as a workflow. Reliable, auditable, with supply chain provenance.

See :doc:`composition` for how compositions work.

See :doc:`pipelines` for when and why to use pipeline execution.

Module Types
------------

The functionality in your solution comes from different sources:

**Batteries-Included**
    Ready-made modules from the Julee framework. CEAP workflows, repository implementations, service integrations.

**Third-Party**
    External modules you import or integrate. Can be embedded (run in your process) or dispatched (called as services).

**Domain-Specific**
    Your own code implementing business logic specific to your solution.

See :doc:`modules` for how modules integrate into solutions.

See :doc:`batteries-included` for what Julee provides out of the box.

See :doc:`3rd-party` for integrating external modules.

Solution Architecture
---------------------

A typical Julee solution looks like this:

::

    ┌─────────────────────────────────────────────────────────┐
    │                    Julee Solution                       │
    ├─────────────────────────────────────────────────────────┤
    │  Applications                                           │
    │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
    │  │ Worker  │ │   API   │ │   CLI   │ │   UI    │       │
    │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │
    │       │           │           │           │             │
    │       └───────────┴─────┬─────┴───────────┘             │
    │                         │                               │
    │  Compositions (Use Cases + Services)                    │
    │  ┌──────────────────────┴──────────────────────┐       │
    │  │  Domain Use Cases                           │       │
    │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐       │       │
    │  │  │ Extract │ │Validate │ │ Custom  │       │       │
    │  │  └─────────┘ └─────────┘ └─────────┘       │       │
    │  └──────────────────────┬──────────────────────┘       │
    │                         │                               │
    │  Modules                │                               │
    │  ┌──────────────────────┴──────────────────────┐       │
    │  │ Batteries    │ 3rd Party    │ Domain        │       │
    │  │ (CEAP, etc)  │ (plugins)    │ (your code)   │       │
    │  └─────────────────────────────────────────────┘       │
    │                                                         │
    │  Infrastructure (Repos, Services, DI)                   │
    └─────────────────────────────────────────────────────────┘

Next Steps
----------

- :doc:`composition` - How use cases combine with services
- :doc:`pipelines` - Reliable execution with supply chain provenance
- :doc:`modules` - Module types and integration patterns
- :doc:`/architecture/applications/index` - Application types (Worker, API, CLI, UI)
- :doc:`/architecture/clean_architecture/index` - Underlying layer structure
