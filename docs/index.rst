Julee Framework Documentation
==============================

Welcome to the Julee documentation. **Julee is a Python framework** for building document processing applications using the **Capture, Extract, Assemble, Publish (CEAP)** pattern with Temporal workflows.

What is Julee?
--------------

Julee is a framework, not an application. You install Julee as a dependency in your project and use its patterns, abstractions, and utilities to build your own document processing applications.

The CEAP Pattern
~~~~~~~~~~~~~~~~

The Capture, Extract, Assemble, Publish pattern provides a structured approach to document processing:

1. **Capture**: Ingest documents into the system
2. **Extract**: Use AI/knowledge services to extract structured data
3. **Assemble**: Combine extracted data according to specifications
4. **Publish**: Output the assembled content

Why Julee?
~~~~~~~~~~

- **Framework, not a monolith**: Build your application using Julee's components
- **Temporal-native**: Built-in workflow orchestration for long-running processes
- **Clean Architecture**: Protocol-based design with clear separation of concerns
- **Type-safe**: Full Pydantic and mypy support
- **Extensible**: Plug in your own storage, AI services, and business logic

Quick Example
~~~~~~~~~~~~~

Install Julee in your project::

    pip install julee

Define your domain model::

    from pydantic import BaseModel

    class Invoice(BaseModel):
        number: str
        amount: float
        date: str

Create a workflow using Julee::

    from temporalio import workflow
    from julee.workflows import extract_assemble_pattern

    @workflow.defn
    class InvoiceWorkflow:
        @workflow.run
        async def run(self, invoice_id: str) -> dict:
            # Use Julee's patterns and components
            return await extract_assemble_pattern(...)

Framework Components
--------------------

Julee provides these reusable components:

Domain Layer
~~~~~~~~~~~~

- **Base Models**: Pydantic models for common entities (Document, Assembly, etc.)
- **Repository Protocols**: Abstract interfaces for data access
- **Use Case Patterns**: Reusable business logic patterns

Infrastructure Layer
~~~~~~~~~~~~~~~~~~~~

- **MinIO Repository**: S3-compatible object storage implementation
- **Memory Repository**: In-memory storage for testing
- **Temporal Integration**: Activity decorators and workflow patterns

Service Layer
~~~~~~~~~~~~~

- **Knowledge Service Protocol**: Abstraction for AI/LLM services
- **Service Implementations**: Ready-to-use service integrations

Example Application
-------------------

This repository includes a reference application that demonstrates how to build with Julee. The example implements a meeting minutes extraction system and shows:

- How to structure a Julee application
- Workflow implementation patterns
- Knowledge service integration
- Storage configuration
- API layer (optional)

The example is deployable with Docker Compose and includes:

- FastAPI REST API
- React UI
- Temporal worker
- MinIO storage
- Demo data

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   configuration

.. toctree::
   :maxdepth: 2
   :caption: Architecture & Design

   framework
   deployment
   code
   workflows

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   autoapi/index
   autoapi/julee/api/index
   autoapi/julee/domain/index
   autoapi/julee/repositories/index
   autoapi/julee/services/index
   autoapi/julee/workflows/index

.. toctree::
   :maxdepth: 1
   :caption: Contributing

   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
