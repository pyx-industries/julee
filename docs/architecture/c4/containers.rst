Containers
==========

The Julee Framework consists of several containers that work together to
provide framework capabilities and documentation tooling.

Core Framework
--------------

.. define-container:: julee-core
   :system: julee
   :name: Core Framework
   :technology: Python
   :description: Domain models, repositories, and workflow patterns

   The core framework provides:

   - Domain models (Document, Assembly, Policy)
   - Repository protocols and implementations (Memory, MinIO)
   - Temporal workflow patterns and activities
   - Use case orchestration

.. define-container:: julee-api
   :system: julee
   :name: REST API
   :technology: FastAPI
   :description: HTTP API for solution interaction

   Provides REST endpoints for document management, workflow execution,
   and system configuration.

.. define-container:: julee-worker
   :system: julee
   :name: Temporal Worker
   :technology: Python / Temporal SDK
   :description: Executes durable workflows

   Runs Temporal activities and workflows for document processing,
   assembly generation, and policy validation.

Documentation Tools
-------------------

.. define-container:: sphinx-hcd
   :system: julee
   :name: Sphinx HCD Extension
   :technology: Python / Sphinx
   :description: Human-Centered Design documentation directives

   Provides RST directives for defining personas, journeys, epics,
   stories, and applications with automatic cross-referencing.

.. define-container:: sphinx-c4
   :system: julee
   :name: Sphinx C4 Extension
   :technology: Python / Sphinx
   :description: C4 model architecture documentation directives

   Provides RST directives for defining software systems, containers,
   components, relationships, and generating PlantUML diagrams.

.. define-container:: hcd-api
   :system: julee
   :name: HCD REST API
   :technology: FastAPI
   :description: API for HCD documentation entities

   Exposes CRUD operations for personas, journeys, epics, stories,
   and applications to external tools.

.. define-container:: hcd-mcp
   :system: julee
   :name: HCD MCP Server
   :technology: Python / MCP
   :description: Model Context Protocol server for AI assistants

   Enables AI assistants to query and manipulate HCD documentation
   entities through the MCP protocol.

.. define-container:: c4-api
   :system: julee
   :name: C4 REST API
   :technology: FastAPI
   :description: API for C4 architecture entities

   Exposes C4 model elements (systems, containers, components,
   relationships) to external tools.

.. define-container:: c4-mcp
   :system: julee
   :name: C4 MCP Server
   :technology: Python / MCP
   :description: Model Context Protocol server for architecture queries

   Enables AI assistants to query C4 architecture models through
   the MCP protocol.

Container Relationships
-----------------------

.. define-relationship:: core-temporal
   :from: julee-core
   :to: temporal
   :description: Executes workflows via Temporal SDK

.. define-relationship:: core-minio
   :from: julee-core
   :to: minio
   :description: Stores artifacts via S3 protocol

.. define-relationship:: api-core
   :from: julee-api
   :to: julee-core
   :description: Uses domain models and use cases

.. define-relationship:: worker-core
   :from: julee-worker
   :to: julee-core
   :description: Executes workflows using core patterns

.. define-relationship:: hcd-api-sphinx-hcd
   :from: hcd-api
   :to: sphinx-hcd
   :description: Shares domain models with

.. define-relationship:: hcd-mcp-sphinx-hcd
   :from: hcd-mcp
   :to: sphinx-hcd
   :description: Shares domain models with

.. define-relationship:: c4-api-sphinx-c4
   :from: c4-api
   :to: sphinx-c4
   :description: Shares domain models with

.. define-relationship:: c4-mcp-sphinx-c4
   :from: c4-mcp
   :to: sphinx-c4
   :description: Shares domain models with

Container Diagram
-----------------

.. container-diagram:: julee
