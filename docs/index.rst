Julee Documentation
===================

Welcome to the Julee documentation. Julee is a **Capture, Extract, Assemble, Publish (CEAP)** workflow system built on Temporal.

Overview
--------

Julee provides a structured workflow for processing documents through AI-powered extraction and assembly:

1. **Capture**: Ingest documents into the system
2. **Extract**: Use knowledge services to extract structured data
3. **Assemble**: Combine extracted data according to specifications
4. **Publish**: Output the assembled content

Architecture
------------

The application follows clean architecture principles with clear separation of concerns:

.. mermaid::

   graph TB
       UI[React UI<br/>Port 3000]
       API[FastAPI<br/>Port 8000]
       Worker[Temporal Worker]
       Temporal[Temporal Server<br/>Port 7233]
       MinIO[MinIO Storage<br/>Port 9000]
       DB[(PostgreSQL<br/>Temporal)]

       UI --> API
       API --> Temporal
       Worker --> Temporal
       API --> MinIO
       Worker --> MinIO
       Temporal --> DB

Key Components
--------------

Domain Layer
~~~~~~~~~~~~

The domain layer contains the core business logic and models:

- **Models**: Pydantic models for type-safe data structures
- **Repositories**: Abstract interfaces for data access
- **Use Cases**: Business logic orchestration

API Layer
~~~~~~~~~

FastAPI-based REST API providing:

- Knowledge service configuration management
- Document management
- Assembly specification CRUD operations
- Workflow execution triggers

Temporal Workers
~~~~~~~~~~~~~~~~

Background workers that execute:

- Document extraction workflows
- Assembly workflows
- Validation workflows

Storage
~~~~~~~

- **MinIO**: Object storage for documents and specifications
- **PostgreSQL**: Temporal workflow state (via Temporal server)

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

   architecture
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
