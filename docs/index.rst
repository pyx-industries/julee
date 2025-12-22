Julee Framework Documentation
==============================

Welcome to the Julee documentation. **Julee is a Python framework** for building accountable and transparent digital supply chains using Temporal workflows.

What is Julee?
--------------

**A reusable framework and a business application are different beasts.**
One is a vocabulary for building things; the other is the thing being built.

Julee is a framework—a vocabulary. You install Julee as a dependency in your project and use its patterns, abstractions, and utilities to build resilient, auditable business processes. Those applications (solutions) are organised around your business domain, using Julee's vocabulary to express your specific needs.

Use Julee when processes must be done correctly, may be complex or long-running, need compliance audit trails (responsible AI, algorithmic due-diligence), or depend on unreliable services that may fail, timeout, or be rate-limited.

Core Concepts
~~~~~~~~~~~~~

- **Solutions** are applications built with Julee, organised around your bounded contexts
- **Accelerators** are collections of pipelines that automate a business area while maintaining audit trails
- **Pipelines** are use cases wrapped with Temporal, providing durability, reliability, observability, and supply chain provenance

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

See :doc:`architecture/framework` to understand Julee's philosophy, or :doc:`architecture/solutions/index` to learn how to structure your application.

Example Application
-------------------

This repository includes a reference application that demonstrates how to build with Julee. The example implements a meeting minutes extraction system using the CEAP contrib module and shows:

- How to structure a Julee application
- Workflow implementation patterns
- Knowledge service integration
- Storage configuration

The example is deployable with Docker Compose—run ``docker compose up --build`` to explore.

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: Architecture

   architecture/framework
   architecture/c4/index
   architecture/solutions/index
   architecture/clean_architecture/index
   architecture/applications/index

.. toctree::
   :maxdepth: 2
   :caption: Users

   users/index

.. toctree::
   :maxdepth: 2
   :caption: Domain

   domain/index

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   autoapi/index
   autoapi/julee/ceap/domain/index
   autoapi/julee/hcd/index
   autoapi/julee/c4/index
   autoapi/julee/shared/index
   autoapi/julee/repositories/index
   autoapi/julee/services/index
   autoapi/julee/workflows/index
   autoapi/julee/util/index
   autoapi/apps/api/index
   autoapi/apps/mcp/index
   autoapi/apps/sphinx/index

.. toctree::
   :maxdepth: 1
   :caption: Contributing

   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
