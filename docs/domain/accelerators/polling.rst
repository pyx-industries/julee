Polling
=======

.. define-accelerator:: polling
   :status: active

   Contrib module for polling external data sources. Provides a reusable
   pattern for periodically fetching data from HTTP endpoints and
   processing it through Temporal workflows.

   Located at ``src/julee/contrib/polling/``.

   **Capabilities:**

   - Configure polling intervals and retry policies
   - HTTP polling with authentication support
   - Integration with Temporal for durable execution
   - Workflow state tracking across poll cycles
