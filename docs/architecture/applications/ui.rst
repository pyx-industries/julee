UI Applications
===============

.. note::
   This page is a stub. Content to be developed.

UI applications provide user interfaces for Julee solutions.

Overview
--------

UI applications:

- Provide human interaction with the system
- Call API applications (not use cases directly)
- Visualize data and workflow status
- Manage configuration and policies

UI applications are separate from the Julee framework itself - they're clients of the API.

Architecture
------------

::

    ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
    │     UI      │ ──── │     API     │ ──── │   Domain    │
    │  (React,    │ HTTP │  (FastAPI)  │  DI  │ (Use Cases) │
    │   Vue, etc) │      │             │      │             │
    └─────────────┘      └─────────────┘      └─────────────┘

UIs don't have direct access to:

- Domain use cases
- Repositories
- Services
- Temporal workflows

UIs interact with the system exclusively through the API.

Common Patterns
---------------

**Workflow Monitoring**
    Display workflow status, progress, and results via API polling or websockets.

**Document Management**
    Upload, list, view documents via API endpoints.

**Configuration**
    Create and edit assembly specifications, policies, service configs.

**Results Visualization**
    Display extracted data, assemblies, validation results.

Technology Choices
------------------

Julee is framework-agnostic for UIs. Common choices:

- **React** - Component-based, large ecosystem
- **Vue** - Approachable, good documentation
- **Svelte** - Compiled, minimal runtime
- **HTMX** - Server-rendered, minimal JavaScript

The example application in Julee uses React.

See Also
--------

- :doc:`api` for the API layer
- :doc:`/architecture/deployment` for deployment patterns
