Applications
============

Applications are the entry points to a Julee solution. They turn :doc:`use cases </architecture/clean_architecture/use_cases>` into features that users or external systems can access.

A typical Julee solution includes multiple application types: :doc:`workers <worker>` execute long-running pipelines via Temporal, :doc:`APIs <api>` expose use cases as REST endpoints, :doc:`CLIs <cli>` provide command-line access for administration and development, and :doc:`UIs <ui>` provide human interfaces that interact via the API.

All application types wire the same domain use cases. The application type determines *how* use cases are invoked, not *what* business logic runs.

.. toctree::
   :maxdepth: 1
   :hidden:

   worker
   api
   cli
   ui
