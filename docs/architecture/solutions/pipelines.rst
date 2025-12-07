Pipelines
=========

A **Julee pipeline** is a use case
that has been appropriately treated (with decorators and proxies)
to run as a Temporal workflow.

A pipeline is the marriage of two things:

1. A **Julee use case** - deterministic business logic following Clean Architecture
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
The proxies route repository and service calls through Temporal activities,
providing automatic retries, state persistence, and audit trails.

See :py:class:`~julee.workflows.extract_assemble.ExtractAssembleWorkflow` for the CEAP pipeline implementation.


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
    Workflow state is persisted. If the worker crashes, another worker picks up where it left off.

**Observability**
    Julee uses Temporal's workflow history as an audit log. Every step is recorded: what happened, when, with what inputs and outputs.

**Supply Chain Provenance**
    The audit log is used to construct a supply chain provenance graph for artefacts produced by the pipeline. Every step is recorded with its actor, inputs, outputs, and timing - creating a complete lineage for compliance.

Pipeline Proxies
----------------

The magic is in the **pipeline proxies**.
When a use case runs as a pipeline,
its :doc:`repository </architecture/clean_architecture/repositories>` and
:doc:`service </architecture/clean_architecture/services>` dependencies
are replaced with proxy classes that route calls through Temporal activities.

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

The proxy implements the same :doc:`protocol </architecture/clean_architecture/protocols>`,
so the use case doesn't know the difference.
But each method call becomes a Temporal activity with:

- Its own **timeout**
- Its own **retry policy**
- **State persistence** in Temporal's history
- **Audit trail** of inputs and outputs

Julee provides decorators to generate these proxies automatically:

- :py:func:`~julee.util.temporal.decorators.temporal_workflow_proxy` - generates proxy classes from protocols
- :py:func:`~julee.util.temporal.decorators.temporal_activity_registration` - wraps repository/service methods as activities

The pipeline uses Temporal's ``@workflow.defn`` and ``@workflow.run`` decorators to wrap the use case.
See :py:class:`~julee.workflows.extract_assemble.ExtractAssembleWorkflow` for the CEAP pipeline implementation

Dispatching Pipelines
---------------------

Applications dispatch pipelines rather than executing compositions directly.

From API Applications
~~~~~~~~~~~~~~~~~~~~~

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

Applications can choose how to execute use cases:

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
