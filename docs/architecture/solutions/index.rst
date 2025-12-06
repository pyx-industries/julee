Solutions
=========

A **Julee Solution** is a software system built using the Julee framework—see :doc:`/architecture/framework` for what that means. This section covers how solutions are structured.

.. toctree::
   :maxdepth: 1
   :caption: Topics

   composition
   pipelines
   modules
   batteries-included
   3rd-party

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

See :doc:`composition` for details. See :doc:`pipelines` for when and why to use pipeline execution.

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
