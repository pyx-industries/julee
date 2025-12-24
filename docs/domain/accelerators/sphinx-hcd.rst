HCD Accelerator
===============

.. define-accelerator:: hcd
   :name: HCD Accelerator
   :status: active
   :concepts: Persona, Journey, Epic, Story, App, Accelerator, Integration
   :path: src/julee/hcd/
   :technology: Python

   Human-Centered Design bounded context for documenting solutions from
   a user perspective. Provides domain models, repositories, and use cases
   for managing personas, journeys, epics, stories, applications, accelerators,
   and integrations.

   **Capabilities:**

   - Define document-first entities (personas, journeys, epics, stories)
   - Parse code-first entities (apps from YAML, stories from Gherkin)
   - Generate index pages and relationship diagrams
   - Validate documentation coverage at build time
   - RST repository backend for lossless round-trip editing

Domain Entities
---------------

.. accelerator-entity-list:: hcd

Entity Diagram
~~~~~~~~~~~~~~

.. entity-diagram:: hcd

Use Cases
---------

.. accelerator-usecase-list:: hcd

Code Reference
--------------

.. list-accelerator-code:: hcd
