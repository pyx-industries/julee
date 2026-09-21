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

    pip install julee            # the framework: pydantic only
    pip install "julee[all]"     # every integration

Julee installs a small kernel. Add what your solution uses, with the
``doctrine``, ``temporal``, ``api`` and ``minio`` extras.

Domain code ships as kits, which a solution installs and then adopts in
``[tool.julee] kits``. See `julee-kits
<https://github.com/pyx-industries/julee-kits>`_.

Julee applications require: `Temporal <https://temporal.io/>`_ (workflow orchestration), S3-compatible object storage (e.g. MinIO), PostgreSQL (for Temporal).

See :doc:`architecture/framework` to understand Julee's philosophy, or :doc:`architecture/solutions/index` to learn how to structure your application.

Example Application
-------------------

The `CEAP kit <https://github.com/pyx-industries/julee-kits/tree/master/ceap>`_
is the reference application: a meeting minutes extraction system that shows
how a solution is structured, how use cases become durable pipelines, how a
knowledge service is integrated and how storage is configured. It ships a
Docker Compose stack to explore it with.

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: Architecture

   architecture/framework
   architecture/solutions/index
   architecture/clean_architecture/index
   architecture/applications/index

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   autoapi/index

.. toctree::
   :maxdepth: 1
   :caption: Contributing

   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
