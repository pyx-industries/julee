Workflows
=========

**CEAP workflows demonstrate Julee's patterns for document processing.**

This page documents the Capture, Extract, Assemble, Publish pattern and its implementation as Temporal workflows.

The CEAP Pattern
----------------

**CEAP provides a structured approach to AI-driven document processing.**

The Four Phases
~~~~~~~~~~~~~~~

**1. Capture**
    Ingest documents into the system. Documents enter as files, PDFs, images, text.

**2. Extract**
    Use AI/knowledge services to extract structured data from documents. This is where LLMs read and understand content.

**3. Assemble**
    Combine extracted data according to specifications. Structure the raw AI output into your domain model.

**4. Publish**
    Output the assembled content. Store results, trigger downstream processes, generate reports.

Why CEAP?
~~~~~~~~~

**Separates Concerns**
    Each phase has one job. Capture doesn't care about AI. Extract doesn't care about output format.

**Handles Failures**
    AI services fail. CEAP workflows use Temporal to handle retries and recovery automatically.

**Maintains Audit Trails**
    Every step is recorded. See exactly what happened, when, and why.

**Enables Testing**
    Test each phase independently. Mock AI for unit tests, use real AI for integration tests.

Included Workflows
------------------

Julee provides two example workflows:

:py:class:`~julee.workflows.extract_assemble.ExtractAssembleWorkflow`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Process documents through the CEAP pipeline.

Implements Capture, Extract, Assemble, and Publish for AI-driven document processing.

**Steps:**

1. **Capture**: Retrieve document from storage
2. **Capture**: Retrieve assembly specification
3. **Capture**: Fetch knowledge service configuration
4. **Extract**: Execute AI queries on document
5. **Assemble**: Combine results per specification
6. **Publish**: Store final assembly

**Execution:**

Via API::

    POST /workflows/extract-assemble
    {
      "document_id": "doc-123",
      "specification_id": "spec-456"
    }

Via Temporal client::

    from temporalio.client import Client
    from julee.workflows import ExtractAssembleWorkflow

    client = await Client.connect("localhost:7233")

    result = await client.execute_workflow(
        ExtractAssembleWorkflow.run,
        args=[document_id, specification_id],
        id=f"extract-assemble-{document_id}",
        task_queue="julee-extract-assemble-queue"
    )

**Workflow diagram:**

.. mermaid::

   stateDiagram-v2
       [*] --> FetchDocument
       FetchDocument --> FetchSpecification
       FetchSpecification --> FetchKnowledgeConfig
       FetchKnowledgeConfig --> ExtractData
       ExtractData --> AssembleData
       AssembleData --> StoreResult
       StoreResult --> [*]

       ExtractData --> Error: AI service fails
       Error --> Retry
       Retry --> ExtractData: Backoff & retry

**Activities:**

``fetch_document(document_id)``
    Retrieve document from repository.

``fetch_specification(specification_id)``
    Retrieve assembly specification from repository.

``fetch_knowledge_service_config(config_id)``
    Get knowledge service configuration.

``extract_data(document, queries, config)``
    Execute AI queries via knowledge service. This is the Extract phase.

``assemble_data(extracted_data, specification)``
    Combine extracted data per specification. This is the Assemble phase.

``store_assembly(assembly)``
    Persist assembled result via repository. This is the Publish phase.

**Error Handling:**

Temporal automatically retries failed activities with exponential backoff:

- AI service rate limits: Wait and retry
- Network timeouts: Retry with longer timeout
- Temporary failures: Automatic recovery

Retry policy::

    RetryPolicy(
        initial_interval=timedelta(seconds=1),
        maximum_interval=timedelta(seconds=60),
        backoff_coefficient=2.0,
        maximum_attempts=5
    )

:py:class:`~julee.workflows.validate_document.ValidateDocumentWorkflow`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Validate documents against policies.

Ensures compliance and policy enforcement with audit trails.

**Steps:**

1. Retrieve document from storage
2. Fetch validation policy
3. Execute validation rules
4. Record validation results for accountability

**Execution:**

Via API::

    POST /workflows/validate-document
    {
      "document_id": "doc-123",
      "policy_id": "policy-456"
    }

**Workflow diagram:**

.. mermaid::

   stateDiagram-v2
       [*] --> FetchDocument
       FetchDocument --> FetchPolicy
       FetchPolicy --> ExecuteValidation
       ExecuteValidation --> StoreValidationResult
       StoreValidationResult --> [*]

       ExecuteValidation --> ValidationFailed: Policy violation
       ValidationFailed --> StoreValidationResult: Record failure

**Activities:**

``fetch_document(document_id)``
    Retrieve document to validate.

``fetch_policy(policy_id)``
    Get validation policy rules.

``execute_validation(document, policy)``
    Run validation checks. Returns validation result with:

    - ``is_valid``: Boolean
    - ``violations``: List of policy violations
    - ``metadata``: Additional validation info

``store_validation_result(result)``
    Persist validation outcome for audit trail.

Using the Workflows
-------------------

Configuration
~~~~~~~~~~~~~

Workflows use repositories and services via :doc:`dependency injection </architecture/clean_architecture/protocols>`.

**Example configuration:**

::

    # In dependencies.py
    def get_document_repository() -> DocumentRepository:
        return MinioDocumentRepository(get_minio_client())

    def get_knowledge_service() -> KnowledgeService:
        return AnthropicKnowledgeService(
            api_key=settings.anthropic_api_key
        )

    # Workflows use these via DI

Customization
~~~~~~~~~~~~~

**Use as-is:**

Default workflows work with configuration only::

    # Set environment variables
    ANTHROPIC_API_KEY=your-key
    MINIO_ENDPOINT=localhost:9000

    # Run worker with default workflows
    worker = Worker(
        client,
        task_queue="julee-extract-assemble-queue",
        workflows=[ExtractAssembleWorkflow],
        activities=get_all_activities()
    )

**Extend workflows:**

Create custom workflows using Julee's patterns::

    from temporalio import workflow
    from julee.workflows import ExtractAssembleWorkflow

    @workflow.defn
    class CustomExtractWorkflow(ExtractAssembleWorkflow):
        @workflow.run
        async def run(self, document_id: str, spec_id: str):
            # Custom pre-processing
            await self.preprocess(document_id)

            # Call parent workflow
            result = await super().run(document_id, spec_id)

            # Custom post-processing
            await self.postprocess(result)

            return result

**Build new workflows:**

Create workflows using Julee's use cases::

    from temporalio import workflow
    from julee.domain.use_cases import ExtractAssembleUseCase

    @workflow.defn
    class MyCustomWorkflow:
        @workflow.run
        async def run(self, doc_id: str):
            # Your custom logic
            processed_doc = await workflow.execute_activity(
                my_custom_activity,
                doc_id
            )

            # Use Julee's use case
            result = await workflow.execute_activity(
                extract_assemble_activity,
                processed_doc
            )

            return result

Monitoring
----------

Temporal UI
~~~~~~~~~~~

Access Temporal UI at http://localhost:8001 to:

- View running workflows
- Inspect workflow execution history
- See activity logs and errors
- Retry failed workflows
- Cancel workflows

**Workflow history shows:**

- Every activity execution
- Retry attempts
- Error messages
- Timing information
- Input/output data

Workflow Status
~~~~~~~~~~~~~~~

Check workflow status via API::

    GET /workflows/{workflow_id}/status

Returns::

    {
      "workflow_id": "extract-assemble-doc-123",
      "status": "running",  # or "completed", "failed", "cancelled"
      "started_at": "2025-12-05T10:00:00Z",
      "updated_at": "2025-12-05T10:01:30Z"
    }

Queries
~~~~~~~

Workflows can expose queries to inspect state without completing::

    @workflow.query
    def get_progress(self) -> dict:
        """Query workflow progress without waiting for completion."""
        return {
            "step": self.current_step,
            "progress_percentage": self.progress
        }

Query from client::

    result = await client.query_workflow(
        ExtractAssembleWorkflow.get_progress,
        workflow_id="extract-assemble-doc-123"
    )

Testing Workflows
-----------------

Unit Testing
~~~~~~~~~~~~

Test workflow logic with Temporal's test environment::

    from temporalio.testing import WorkflowEnvironment
    from julee.workflows import ExtractAssembleWorkflow

    @pytest.mark.asyncio
    async def test_extract_assemble_workflow():
        async with WorkflowEnvironment() as env:
            # Use test activities with mocks
            activities = create_test_activities(
                doc_repo=MemoryDocumentRepository(),
                knowledge=MemoryKnowledgeService()
            )

            # Execute workflow
            result = await env.client.execute_workflow(
                ExtractAssembleWorkflow.run,
                args=["doc-id", "spec-id"],
                task_queue="test-queue"
            )

            assert result.status == "completed"

Testing uses :doc:`protocol-based </architecture/clean_architecture/protocols>` dependency injection.

Integration Testing
~~~~~~~~~~~~~~~~~~~

Test with real Temporal server::

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_workflow_with_real_temporal():
        # Connect to test Temporal server
        client = await Client.connect("localhost:7233")

        # Start worker with test activities
        worker = Worker(
            client,
            task_queue="test-queue",
            workflows=[ExtractAssembleWorkflow],
            activities=create_activities(
                doc_repo=MinioDocumentRepository(test_client),
                knowledge=MemoryKnowledgeService()  # Mock expensive AI
            )
        )

        # Execute workflow
        async with worker:
            result = await client.execute_workflow(
                ExtractAssembleWorkflow.run,
                args=["test-doc", "test-spec"],
                id="test-workflow-1",
                task_queue="test-queue"
            )

        assert result is not None

Best Practices
--------------

Workflow Design
~~~~~~~~~~~~~~~

**Deterministic Execution**
    Workflows must be deterministic for replay. No random numbers, no wall clock reads, no external API calls in workflow code.

**Activities for Side Effects**
    Put all side effects (API calls, database access) in activities, not workflows.

**Timeouts**
    Set appropriate timeouts for all activities. Default timeouts might be too long.

**State Management**
    Keep workflow state minimal. Store large data in repositories, reference by ID.

Activity Design
~~~~~~~~~~~~~~~

**Single Responsibility**
    Each activity does one thing. Easier to retry, easier to test.

**Idempotent**
    Activities should be safe to retry. Check if work is already done before doing it again.

**Short Duration**
    Keep activities focused. Break long operations into multiple activities.

**Error Messages**
    Log detailed error information. Temporal preserves activity errors in workflow history.

Error Handling
~~~~~~~~~~~~~~

**Expected Errors**
    Handle business errors explicitly. Workflow should decide what to do.

**Transient Failures**
    Use Temporal's retry policies for temporary failures (network, rate limits).

**Fatal Errors**
    Fail fast for unrecoverable errors. Don't retry endlessly.

**Compensation**
    Implement cleanup for partial failures. Undo operations if workflow fails midway.

Advanced Topics
---------------

Workflow Versioning
~~~~~~~~~~~~~~~~~~~

Temporal supports workflow versioning for safe deployments::

    version = workflow.get_version("new-feature", 1, 2)
    if version == 1:
        # Old behavior for existing workflows
        await workflow.execute_activity(old_activity, ...)
    else:
        # New behavior for new workflows
        await workflow.execute_activity(new_activity, ...)

Deploy new code without breaking running workflows.

Child Workflows
~~~~~~~~~~~~~~~

Workflows can start child workflows for modularity::

    result = await workflow.execute_child_workflow(
        ChildWorkflow.run,
        args=[...],
        id=f"child-{parent_workflow_id}"
    )

Use for independent subprocesses that could fail separately.

Signals
~~~~~~~

Send external events to running workflows::

    @workflow.signal
    async def cancel_processing(self):
        """Signal handler to cancel workflow."""
        self.should_cancel = True

    # In workflow run method
    if self.should_cancel:
        return {"status": "cancelled"}

Signal from client::

    await client.signal_workflow(
        ExtractAssembleWorkflow.cancel_processing,
        workflow_id="extract-assemble-doc-123"
    )

Timers
~~~~~~

Workflows can wait for specific durations::

    # Wait 60 seconds before next attempt
    await asyncio.sleep(60)

Temporal manages timers - workflow can wait hours, days, even months.

Continue-As-New
~~~~~~~~~~~~~~~

For very long-running workflows, use continue-as-new to manage history size::

    if iteration_count > 1000:
        # Continue with new workflow execution
        workflow.continue_as_new(args=[new_state])

Prevents workflow history from growing unbounded.

Summary
-------

CEAP workflows (ExtractAssembleWorkflow, ValidateDocumentWorkflow) demonstrate Julee's patterns for document processing. Use as-is, extend, or build custom workflows. Monitor via Temporal UI.
