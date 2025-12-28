Julee Framework Documentation
==============================

Welcome to the Julee documentation. **Julee is a Python framework** for building accountable and transparent digital supply chains using Temporal workflows.

What is Julee?
--------------

**A reusable framework and a business application are different beasts.**
One is a vocabulary for building things; the other is the thing being built.

Julee is a framework—a vocabulary. You install Julee as a dependency in your project and use its patterns, abstractions, and utilities to build resilient, auditable business processes. Those applications (solutions) are organised around your business domain, using Julee's vocabulary to express your specific needs.

Use Julee when processes must be done correctly, may be complex or long-running, need compliance audit trails (responsible AI, algorithmic due-diligence), or depend on unreliable services that may fail, timeout, or be rate-limited.

See :py:mod:`julee` to understand Julee's philosophy.

Core Concepts
~~~~~~~~~~~~~

- :py:mod:`~julee.core.entities.solution` — Applications built with Julee, organised around bounded contexts
- :py:mod:`~julee.core.entities.bounded_context` — Domain boundaries with entities, use cases, and interfaces
- :py:mod:`~julee.core.entities.pipeline` — Use cases wrapped with Temporal for durability and auditability
- :py:mod:`~julee.hcd.entities.accelerator` — Collections of pipelines that automate a business area
- :py:mod:`~julee.core.entities.application` — Entry points (API, CLI, Worker, MCP) that expose capabilities

Why Julee?
~~~~~~~~~~

- **Framework, not a monolith**: Build your application using Julee's components
- **Temporal-native**: Built-in workflow orchestration for long-running processes
- **Clean Architecture**: Protocol-based design with clear separation of concerns
- **Auditable**: Impeccable audit trails that become "digital product passports"
- **Type-safe**: Full Pydantic and mypy support
- **Extensible**: Plug in your own storage, services, and business logic

Quick Start
~~~~~~~~~~~

Install Julee from `PyPI <https://pypi.org/project/julee/>`_::

    pip install julee

Julee applications require: `Temporal <https://temporal.io/>`_ (workflow orchestration), S3-compatible object storage (e.g. MinIO), PostgreSQL (for Temporal).

Example Application
-------------------

This repository includes a reference application that demonstrates how to build with Julee. The example implements a meeting minutes extraction system using the :py:mod:`CEAP contrib module <julee.contrib.ceap>` and shows:

- How to structure a Julee application
- Workflow implementation patterns
- Knowledge service integration
- Storage configuration

The example is deployable with Docker Compose—run ``docker compose up --build`` to explore.

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: Framework

   api/julee

.. toctree::
   :maxdepth: 2
   :caption: Architecture

   architecture/c4/index
   architecture/solutions/index

.. toctree::
   :maxdepth: 2
   :caption: Users

   users/index

.. toctree::
   :maxdepth: 2
   :caption: Domain

   domain/index

.. toctree::
   :maxdepth: 1
   :caption: Contributing

   contributing

.. toctree::
   :maxdepth: 2
   :caption: Proposals

   proposals/framework_taxonomy/index
   proposals/projected_views/index

.. toctree::
   :maxdepth: 2
   :caption: Full API Reference

   api/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
