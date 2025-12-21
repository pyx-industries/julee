Solutions Developer
===================

.. define-persona:: solutions-developer
   :name: Solutions Developer
   :goals:
      Build reliable workflow solutions
      Maintain audit trails for compliance
      Iterate quickly on business logic
   :frustrations:
      Boilerplate infrastructure code
      Unreliable external service integrations
      Lack of visibility into workflow execution
   :jobs-to-be-done:
      Implement business processes as durable workflows
      Expose capabilities via API, CLI, or worker
      Configure retries and error handling
   :uses-apps: api, mcp
   :uses-contrib: polling

   A developer building production systems with Julee. They work within a
   bounded context, implementing use cases that orchestrate business logic.
   They value clear separation between domain logic and infrastructure,
   and rely on Julee's patterns for reliability and testability.
