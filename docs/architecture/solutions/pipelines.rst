Pipelines
=========

A **Julee pipeline** is a :doc:`use case </architecture/clean_architecture/use_cases>`
that has been appropriately treated (with decorators and proxies)
to run as a Temporal workflow.

A pipeline is the marriage of two things:

1. A **Julee use case** - deterministic business logic following :doc:`Clean Architecture </architecture/clean_architecture/index>`
2. **Temporal workflow technology** - durable, reliable execution with automatic retries

All Julee pipelines are Temporal workflows, but not all Temporal workflows are Julee pipelines.
All Julee pipelines are Julee use cases, but not all Julee use cases are pipelines.

::

    # Use case: pure business logic (in domain layer)
    class ExtractAssembleDataUseCase:
        async def assemble_data(self, document_id: str, spec_id: str) -> Assembly:
            # Business logic - no knowledge of Temporal
            ...

    # Pipeline: use case + Temporal treatment (in application layer)
    @workflow.defn
    class ExtractAssemblePipeline:
        @workflow.run
        async def run(self, document_id: str, spec_id: str) -> Assembly:
            # Create use case with workflow-safe proxies
            use_case = ExtractAssembleDataUseCase(
                document_repo=WorkflowDocumentRepositoryProxy(),
                knowledge_service=WorkflowKnowledgeServiceProxy(),
                ...
            )
            # Execute the same business logic with Temporal durability
            return await use_case.assemble_data(document_id, spec_id)

The use case is unaware it's running as a pipeline.
The proxies route calls to the ports that do I/O through Temporal activities,
providing automatic retries, state persistence, and audit trails.
Ports that do no I/O are passed in as they are, and called inline.

See ``ExtractAssembleWorkflow`` for the CEAP pipeline implementation.


Why Pipelines?
--------------

Direct execution of use cases is simple but fragile:

- If the process crashes, work is lost
- If a service fails, the operation fails
- No record of what happened or why
- No way to retry or recover

Pipelines solve these problems:

**Reliability**
    Automatic retries, timeout handling, failure recovery. If a service is temporarily unavailable, the pipeline waits and retries.

**Durability**
    Workflow state is persisted. If the :doc:`worker </architecture/applications/worker>` crashes, another worker picks up where it left off.

**Observability**
    Julee uses Temporal's workflow history as an audit log. Every step is recorded: what happened, when, with what inputs and outputs.

**Supply Chain Provenance**
    The audit log is used to construct a supply chain provenance graph for artefacts produced by the pipeline. Every step is recorded with its actor, inputs, outputs, and timing - creating a complete lineage for compliance.

Pipeline Proxies
----------------

The magic is in the **pipeline proxies**.
When a use case runs as a pipeline,
some of its dependencies are replaced with proxy classes
that route calls through Temporal activities—and some are not.

Which is which is decided by the kind of
:doc:`driven port </architecture/clean_architecture/protocols>`,
not case by case:

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Port
     - In a pipeline
     - Why
   * - :doc:`Repository </architecture/clean_architecture/repositories>`
     - activity
     - does I/O; its answer can differ between replays
   * - :doc:`Service </architecture/clean_architecture/services>`
     - activity
     - the same
   * - :doc:`Oracle </architecture/clean_architecture/oracles>`
     - activity
     - the same
   * - :doc:`Calculator </architecture/clean_architecture/calculators>`
     - inline
     - deterministic: replay recomputes the same answer
   * - :doc:`Witness </architecture/clean_architecture/witnesses>`
     - inline
     - the runtime recorded its answer; replay is told the same
   * - :doc:`Handler </architecture/clean_architecture/handlers>`
     - inline
     - dispatch is an operation Temporal provides itself

The three inline reasons are genuinely different,
which is why the ports have separate names.
A calculator is safe anywhere, workflow or not.
A witness is safe only inside a runtime that records what it said.
A handler's safety belongs to the engine rather than to the protocol.

Here is a real pipeline injecting three ports into one use case,
two of them called inline::

    use_case = PollDataUseCase(
        poller=WorkflowPollerServiceProxy(),  # activity
        handler=self.get_handler(),           # inline
        analyzer=self.get_analyzer(),         # inline
    )

**Never wrap a witness in an activity.**
The value is already in the workflow history,
so the activity would add a round trip
to fetch something the workflow already holds.

::

    # Direct execution: use case calls real repository
    use_case = ExtractAssembleDataUseCase(
        document_repo=MinioDocumentRepository(client),
        ...
    )

    # Pipeline execution: use case calls proxy repository
    use_case = ExtractAssembleDataUseCase(
        document_repo=WorkflowDocumentRepositoryProxy(),
        ...
    )

The proxy implements the same :doc:`protocol </architecture/clean_architecture/protocols>`, enabling :doc:`dependency injection </architecture/clean_architecture/dependency_injection>` to swap implementations without the use case knowing the difference.
Where a port is proxied, each method call becomes a Temporal activity with:

- Its own **timeout**
- Its own **retry policy**
- **State persistence** in Temporal's history
- **Audit trail** of inputs and outputs

Julee provides decorators to generate these proxies automatically:

- :py:func:`~julee.integrations.temporal.decorators.temporal_workflow_proxy` - generates proxy classes from protocols
- :py:func:`~julee.integrations.temporal.decorators.temporal_activity_registration` - wraps a port's methods as activities

Generate proxies only for the ports on the activity row.
A calculator, witness or handler is injected directly.

The pipeline uses Temporal's ``@workflow.defn`` and ``@workflow.run`` decorators to wrap the use case.
See ``ExtractAssembleWorkflow`` for the CEAP pipeline implementation

Dispatching Pipelines
---------------------

:doc:`Applications </architecture/applications/index>` dispatch pipelines rather than executing use cases directly.

From API Applications
~~~~~~~~~~~~~~~~~~~~~

:doc:`APIs </architecture/applications/api>` dispatch pipelines via a Temporal client, returning a workflow ID that clients can use to check status.

::

    @router.post("/documents/{document_id}/extract")
    async def extract_document(
        document_id: str,
        spec_id: str,
        temporal: Client = Depends(get_temporal_client)
    ):
        """Dispatch extraction pipeline."""
        handle = await temporal.start_workflow(
            ExtractAssemblePipeline.run,
            args=[document_id, spec_id],
            id=f"extract-{document_id}-{uuid.uuid4().hex[:8]}",
            task_queue="julee-extract-queue",
        )

        return {
            "workflow_id": handle.id,
            "status": "dispatched",
            "message": "Extraction pipeline started"
        }

    @router.get("/workflows/{workflow_id}")
    async def get_workflow_status(
        workflow_id: str,
        temporal: Client = Depends(get_temporal_client)
    ):
        """Check pipeline status."""
        handle = temporal.get_workflow_handle(workflow_id)
        description = await handle.describe()

        return {
            "workflow_id": workflow_id,
            "status": description.status.name,
            "start_time": description.start_time,
        }

From CLI Applications
~~~~~~~~~~~~~~~~~~~~~

:doc:`CLIs </architecture/applications/cli>` dispatch pipelines for batch operations or administrative tasks, optionally waiting for the result.

::

    @app.command()
    def extract(
        document_id: str,
        spec_id: str,
        wait: bool = False
    ):
        """Dispatch extraction pipeline."""
        client = get_temporal_client()

        handle = asyncio.run(
            client.start_workflow(
                ExtractAssemblePipeline.run,
                args=[document_id, spec_id],
                id=f"extract-{document_id}",
                task_queue="julee-extract-queue",
            )
        )

        typer.echo(f"Pipeline started: {handle.id}")

        if wait:
            result = asyncio.run(handle.result())
            typer.echo(f"Result: {result}")

Direct Execution vs Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`Applications </architecture/applications/index>` can choose how to execute use cases—directly for simplicity, or as a pipeline for reliability and auditability:

::

    @router.post("/documents/{document_id}/extract")
    async def extract_document(
        document_id: str,
        spec_id: str,
        async_mode: bool = False,
        use_case: ExtractAssembleDataUseCase = Depends(get_use_case),
        temporal: Client = Depends(get_temporal_client)
    ):
        if async_mode:
            # Dispatch as pipeline (reliable, auditable)
            handle = await temporal.start_workflow(
                ExtractAssemblePipeline.run,
                args=[document_id, spec_id],
                id=f"extract-{document_id}",
                task_queue="julee-extract-queue",
            )
            return {"pipeline_id": handle.id, "mode": "pipeline"}
        else:
            # Direct execution (simple, fast)
            result = await use_case.assemble_data(document_id, spec_id)
            return {"result": result, "mode": "direct"}
