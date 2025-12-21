Polling
=======

.. define-contrib:: polling
   :name: Polling Workflow
   :technology: Python, Temporal
   :path: src/julee/contrib/polling/

   Reusable pattern for periodically fetching data from HTTP endpoints and
   processing it through Temporal workflows.

   **Capabilities:**

   - Configure polling intervals and retry policies
   - HTTP polling with authentication support
   - Integration with Temporal for durable execution
   - Workflow state tracking across poll cycles
