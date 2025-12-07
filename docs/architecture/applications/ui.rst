UIs
===

UI applications provide user interfaces for Julee solutions. They interact with the system exclusively through the :doc:`API <api>`—UIs don't have direct access to domain use cases, repositories, services, or Temporal workflows.

Julee is framework-agnostic for UIs. The separation between UI and API means any frontend technology (React, Vue, Svelte, HTMX) can be used.

For long-running operations, the API triggers :doc:`worker <worker>` pipelines; the UI can poll for status or receive updates via webhooks. Administrative functions typically handled by :doc:`CLIs <cli>` may also be exposed through the UI when appropriate.
