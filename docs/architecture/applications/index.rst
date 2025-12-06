Applications
============

Applications are the entry points to your Julee solution. They orchestrate use cases from the domain layer and expose them to users or external systems.

.. toctree::
   :maxdepth: 1
   :caption: Application Types

   worker
   api
   cli
   ui

Application Types
-----------------

Julee solutions typically include multiple application types, each serving a different purpose:

**Worker Applications**
    Temporal workers that execute long-running, reliable workflows. Workers poll Temporal for work and execute use cases as workflow activities. This is where CEAP workflows run.

    See :doc:`worker` for details.

**API Applications**
    REST endpoints for external access. APIs execute use cases directly for synchronous operations, or trigger workflows via Temporal client for async operations.

    See :doc:`api` for details.

**CLI Applications**
    Command-line interfaces for operations and administration. CLIs execute use cases from the command line, trigger workflows, and perform administrative tasks.

    See :doc:`cli` for details.

**UI Applications**
    User interfaces (web, desktop, mobile) that interact with API applications. UIs don't directly execute use cases - they call the API.

    See :doc:`ui` for details.

Same Use Cases, Different Entry Points
--------------------------------------

All application types orchestrate the same domain use cases. The application type determines *how* use cases are invoked, not *what* business logic runs.

::

    # Domain Layer - Use Case (same for all applications)
    class ExtractAssembleUseCase:
        async def execute(self, doc_id: str, spec_id: str):
            # Business logic here
            ...

    # Worker Application - via Temporal workflow
    @workflow.defn
    class ExtractAssembleWorkflow:
        @workflow.run
        async def run(self, doc_id: str, spec_id: str):
            return await workflow.execute_activity(
                extract_assemble_activity,
                args=[doc_id, spec_id]
            )

    # API Application - via HTTP endpoint
    @router.post("/extract")
    async def extract_endpoint(
        doc_id: str,
        spec_id: str,
        use_case: ExtractAssembleUseCase = Depends(get_use_case)
    ):
        return await use_case.execute(doc_id, spec_id)

    # CLI Application - via command
    @app.command()
    def extract(doc_id: str, spec_id: str):
        use_case = get_use_case()
        result = asyncio.run(use_case.execute(doc_id, spec_id))
        print(result)

When to Use Each Application Type
---------------------------------

**Use Workers for:**

- Long-running processes (minutes to hours)
- Operations that may fail and need retries
- Processes requiring audit trails
- AI-driven workflows (CEAP pattern)

**Use APIs for:**

- Synchronous request/response operations
- External system integrations
- User-facing operations requiring immediate feedback
- Triggering async workflows

**Use CLIs for:**

- Administrative tasks
- Development and debugging
- Batch operations
- System initialization

**Use UIs for:**

- Human interaction
- Data visualization
- Workflow monitoring
- Configuration management

Deployment Considerations
-------------------------

Each application type has different deployment characteristics:

- **Workers**: Scale based on queue depth, can run multiple instances
- **APIs**: Stateless, scale horizontally behind load balancer
- **CLIs**: Run on-demand, typically on admin machines or in CI/CD
- **UIs**: Static assets, deployed to CDN or web server

For deployment architecture, see :doc:`/architecture/deployment`.

For the underlying layer structure, see :doc:`/architecture/clean_architecture/index`.
