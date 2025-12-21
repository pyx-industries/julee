Containers
==========

Julee Tooling consists of applications that expose accelerators for developing
solutions. Each accelerator is a bounded context with domain models, repositories,
and use cases.

Applications
------------

Applications provide access to the accelerators through different interfaces.

.. app-list-by-interface::

Accelerators
------------

Each accelerator is a bounded context for conceptualising solutions.

.. accelerator-list::

Contrib Modules
---------------

Contrib modules are reusable runtime utilities that solutions can use directly.

.. contrib-list::

Foundation
----------

All accelerators are built on clean architecture idioms:

- Domain models (Pydantic entities)
- Repository protocols (abstract persistence)
- Use cases (application business rules)
- Memory and file-based repository implementations

Container Diagram
-----------------

The following diagram is auto-generated from HCD app and accelerator definitions:

.. c4-container-diagram::
   :title: Container Diagram - Julee Tooling
   :system-name: Julee Tooling
   :show-foundation:
   :show-external:
   :foundation-name: Foundation
   :external-name: External Systems
