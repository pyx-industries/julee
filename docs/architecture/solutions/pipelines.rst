Pipelines
=========

A **pipeline** is a composition executed via Temporal for reliable, auditable execution with supply chain provenance.

Pipelines transform compositions from simple function calls into durable, observable business processes.

Why Pipelines?
--------------

Direct execution of compositions is simple but fragile:

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
    Complete history of every step. What happened, when, with what inputs and outputs.

**Supply Chain Provenance**
    Every step is recorded with its actor, inputs, outputs, and timing. Creates an auditable trail for compliance.

From Composition to Pipeline
----------------------------

A composition becomes a pipeline when wrapped in a Temporal workflow:

::

    # The composition (business logic)
    class ExtractAssembleComposition:
        async def execute(self, document_id: str, spec_id: str) -> Assembly:
            # ... business logic ...

    # The pipeline (Temporal workflow)
    @workflow.defn
    class ExtractAssemblePipeline:
        @workflow.run
        async def run(self, document_id: str, spec_id: str) -> dict:
            # Each step becomes an activity
            document = await workflow.execute_activity(
                fetch_document,
                document_id,
                start_to_close_timeout=timedelta(seconds=30),
            )

            spec = await workflow.execute_activity(
                fetch_specification,
                spec_id,
                start_to_close_timeout=timedelta(seconds=30),
            )

            extracted = await workflow.execute_activity(
                extract_data,
                args=[document, spec],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            assembly = await workflow.execute_activity(
                assemble_and_store,
                args=[document_id, spec_id, extracted],
                start_to_close_timeout=timedelta(seconds=60),
            )

            return assembly

The workflow:

- Breaks the composition into discrete **activities**
- Each activity has its own **timeout** and **retry policy**
- Temporal records **every step** in the workflow history
- If any step fails, Temporal handles **retries** automatically

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

Direct Execution vs Dispatch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Applications can choose:

::

    @router.post("/documents/{document_id}/extract")
    async def extract_document(
        document_id: str,
        spec_id: str,
        async_mode: bool = False,
        composition: ExtractAssembleComposition = Depends(get_composition),
        temporal: Client = Depends(get_temporal_client)
    ):
        if async_mode:
            # Dispatch to pipeline (reliable, auditable)
            handle = await temporal.start_workflow(
                ExtractAssemblePipeline.run,
                args=[document_id, spec_id],
                id=f"extract-{document_id}",
                task_queue="julee-extract-queue",
            )
            return {"workflow_id": handle.id, "mode": "pipeline"}
        else:
            # Direct execution (simple, fast)
            result = await composition.execute(document_id, spec_id)
            return {"result": result, "mode": "direct"}

Supply Chain Provenance
-----------------------

Pipelines create high-integrity supply chain information through Temporal's workflow history.

What is Recorded
~~~~~~~~~~~~~~~~

Every pipeline execution records:

**Workflow Metadata**
    - Workflow ID (unique identifier)
    - Start time, end time, duration
    - Input parameters
    - Final result or error

**Activity Execution**
    - Activity name (what was done)
    - Start time, end time, duration
    - Input parameters
    - Output result
    - Retry attempts (if any)
    - Worker identity (who executed it)

**Supply Chain Actors**
    - Which services were called
    - Which workers executed activities
    - External service responses

This creates a complete **audit trail** for every operation.

Example Workflow History
~~~~~~~~~~~~~~~~~~~~~~~~

::

    Workflow: extract-doc-123
    Started: 2025-12-06T10:00:00Z
    Status: Completed

    Activities:
    1. fetch_document
       - Started: 10:00:00.100
       - Completed: 10:00:00.250
       - Worker: worker-1
       - Input: document_id="doc-123"
       - Output: Document(id="doc-123", name="Invoice.pdf")

    2. fetch_specification
       - Started: 10:00:00.260
       - Completed: 10:00:00.310
       - Worker: worker-1
       - Input: spec_id="invoice-spec"
       - Output: Specification(id="invoice-spec", ...)

    3. extract_data
       - Started: 10:00:00.320
       - Completed: 10:00:45.100
       - Worker: worker-2
       - Input: document, specification
       - Output: {extracted_fields...}
       - Service Called: Anthropic Claude
       - Retry Attempts: 0

    4. assemble_and_store
       - Started: 10:00:45.110
       - Completed: 10:00:45.500
       - Worker: worker-2
       - Input: document_id, spec_id, extracted_data
       - Output: Assembly(id="assembly-456")

    Result: Assembly(id="assembly-456")
    Duration: 45.5 seconds

Digital Product Passport
~~~~~~~~~~~~~~~~~~~~~~~~

This history can be transformed into a **digital product passport** - a document that accompanies the output and proves:

- What input was processed
- What steps were taken
- Which services were used
- When each step occurred
- Who (which worker/service) performed each step

For compliance-critical applications, this provenance is essential.

Reliability Patterns
--------------------

Retry Policies
~~~~~~~~~~~~~~

Configure how activities handle failures:

::

    # Aggressive retries for transient failures
    ai_retry_policy = RetryPolicy(
        initial_interval=timedelta(seconds=1),
        maximum_interval=timedelta(seconds=60),
        backoff_coefficient=2.0,
        maximum_attempts=5,
    )

    # Single attempt for operations that shouldn't retry
    no_retry_policy = RetryPolicy(
        maximum_attempts=1,
    )

    # In workflow
    result = await workflow.execute_activity(
        extract_data,
        args=[document, spec],
        start_to_close_timeout=timedelta(minutes=5),
        retry_policy=ai_retry_policy,
    )

Timeouts
~~~~~~~~

Set appropriate timeouts for each activity:

::

    # Fast operations
    document = await workflow.execute_activity(
        fetch_document,
        document_id,
        start_to_close_timeout=timedelta(seconds=30),
    )

    # Slow AI operations
    extracted = await workflow.execute_activity(
        extract_data,
        args=[document, spec],
        start_to_close_timeout=timedelta(minutes=10),
    )

    # Very long operations
    result = await workflow.execute_activity(
        process_large_batch,
        batch_id,
        start_to_close_timeout=timedelta(hours=1),
    )

Heartbeats
~~~~~~~~~~

For long-running activities, use heartbeats to report progress:

::

    @activity.defn
    async def process_large_document(document_id: str) -> dict:
        document = await fetch_document(document_id)

        results = []
        for i, page in enumerate(document.pages):
            # Report progress
            activity.heartbeat(f"Processing page {i+1}/{len(document.pages)}")

            result = await process_page(page)
            results.append(result)

        return {"pages": results}

If the worker crashes, Temporal knows the activity was still running (heartbeat stopped) and can reschedule it.

When to Use Pipelines
---------------------

**Use pipelines when:**

- Operations involve unreliable services (AI, external APIs)
- Operations are long-running (minutes to hours)
- Audit trails are required
- Compliance requires supply chain provenance
- Failures must be handled gracefully
- Operations must complete eventually (at-least-once)

**Use direct execution when:**

- Operations are fast and simple
- Failure is acceptable (can retry manually)
- No audit trail needed
- Development and testing

Worker Applications
-------------------

Pipelines run on **Worker applications** - processes that poll Temporal for work.

::

    # worker.py
    from temporalio.client import Client
    from temporalio.worker import Worker

    async def run_worker():
        client = await Client.connect("localhost:7233")

        worker = Worker(
            client,
            task_queue="julee-extract-queue",
            workflows=[ExtractAssemblePipeline, ValidateDocumentPipeline],
            activities=[
                fetch_document,
                fetch_specification,
                extract_data,
                assemble_and_store,
            ],
        )

        await worker.run()

See :doc:`/architecture/applications/worker` for Worker application details.

Summary
-------

**Pipelines make compositions reliable and auditable.**

- Wrap compositions in Temporal workflows
- Break operations into activities with timeouts and retries
- Record complete history for supply chain provenance
- Enable compliance through audit trails

**Key principle:** Applications dispatch pipelines for reliable execution. Workers execute the actual work. Temporal manages state, retries, and history.

For composition patterns, see :doc:`composition`.

For Worker applications, see :doc:`/architecture/applications/worker`.

For CEAP workflows (batteries-included pipelines), see :doc:`batteries-included`.
