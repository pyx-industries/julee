System Context
==============

The Julee Framework is a Python framework for building accountable and
transparent digital supply chains using Temporal workflows.

.. define-software-system:: julee
   :name: Julee Framework
   :description: Python framework for building accountable workflow solutions

   Julee provides reusable patterns, abstractions, and utilities for building
   resilient, auditable business processes. Solutions built with Julee maintain
   impeccable audit trails that become "digital product passports".

External Systems
----------------

.. define-software-system:: temporal
   :name: Temporal
   :description: Workflow orchestration platform
   :external: true

   Provides durable execution, retries, and workflow state management.

.. define-software-system:: minio
   :name: MinIO / S3
   :description: Object storage for documents and artifacts
   :external: true

   S3-compatible storage for documents, assemblies, and workflow artifacts.

.. define-software-system:: postgresql
   :name: PostgreSQL
   :description: Relational database for Temporal persistence
   :external: true

   Provides persistence layer for Temporal workflow state.

Relationships
-------------

.. define-relationship:: julee-temporal
   :from: julee
   :to: temporal
   :description: Orchestrates workflows via

.. define-relationship:: julee-minio
   :from: julee
   :to: minio
   :description: Stores documents and artifacts in

.. define-relationship:: temporal-postgresql
   :from: temporal
   :to: postgresql
   :description: Persists workflow state to

System Context Diagram
----------------------

.. system-context-diagram:: julee
