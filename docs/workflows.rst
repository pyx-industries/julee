Workflows
=========

Overview
--------

Julee uses Temporal workflows to orchestrate long-running, stateful processes for document processing.

Extract and Assemble Workflow
------------------------------

The primary workflow for processing documents through the CEAP pipeline.

Purpose
~~~~~~~

Extract structured data from documents using knowledge services and assemble it according to specifications.

Workflow Definition
~~~~~~~~~~~~~~~~~~~

``ExtractAssembleWorkflow`` orchestrates:

1. Document retrieval
2. Specification retrieval
3. Knowledge service configuration lookup
4. Data extraction via knowledge services
5. Data assembly according to specification
6. Result storage

Execution
~~~~~~~~~

Start via API::

    POST /workflows/extract-assemble
    {
      "document_id": "doc-123",
      "specification_id": "spec-456"
    }

Or programmatically::

    from temporalio.client import Client
    from workflows import ExtractAssembleWorkflow

    client = await Client.connect("localhost:7233")

    result = await client.execute_workflow(
        ExtractAssembleWorkflow.run,
        args=[document_id, specification_id],
        id=f"extract-assemble-{document_id}",
        task_queue="julee-extract-assemble-queue"
    )

Workflow Steps
~~~~~~~~~~~~~~

.. mermaid::

   stateDiagram-v2
       [*] --> FetchDocument
       FetchDocument --> FetchSpecification
       FetchSpecification --> FetchKnowledgeConfig
       FetchKnowledgeConfig --> ExtractData
       ExtractData --> AssembleData
       AssembleData --> StoreResult
       StoreResult --> [*]

       ExtractData --> Error: Extraction fails
       Error --> Retry
       Retry --> ExtractData: Backoff

Activities
~~~~~~~~~~

The workflow executes these activities:

**fetch_document**
    Retrieve document from storage.

    - Input: ``document_id``
    - Output: ``Document``

**fetch_specification**
    Retrieve assembly specification.

    - Input: ``specification_id``
    - Output: ``AssemblySpecification``

**fetch_knowledge_service_config**
    Get knowledge service configuration.

    - Input: ``config_id``
    - Output: ``KnowledgeServiceConfig``

**extract_data**
    Execute knowledge service queries.

    - Input: ``document``, ``queries``, ``config``
    - Output: ``dict`` of extracted data

**assemble_data**
    Combine extracted data per specification.

    - Input: ``extracted_data``, ``specification``
    - Output: ``Assembly``

**store_assembly**
    Persist assembled result.

    - Input: ``assembly``
    - Output: ``Assembly``

Error Handling
~~~~~~~~~~~~~~

The workflow implements retry logic for transient failures:

- Knowledge service rate limits
- Network timeouts
- Temporary storage issues

Retry Policy::

    retry_policy=RetryPolicy(
        initial_interval=timedelta(seconds=1),
        maximum_interval=timedelta(seconds=60),
        backoff_coefficient=2.0,
        maximum_attempts=5,
    )

Validate Document Workflow
---------------------------

Validates documents against defined policies.

Purpose
~~~~~~~

Check document content, structure, and metadata against validation rules.

Workflow Definition
~~~~~~~~~~~~~~~~~~~

``ValidateDocumentWorkflow`` performs:

1. Document retrieval
2. Policy retrieval
3. Validation execution
4. Result recording

Execution
~~~~~~~~~

Start via API::

    POST /workflows/validate-document
    {
      "document_id": "doc-123",
      "policy_id": "policy-456"
    }

Workflow Steps
~~~~~~~~~~~~~~

.. mermaid::

   stateDiagram-v2
       [*] --> FetchDocument
       FetchDocument --> FetchPolicy
       FetchPolicy --> ExecuteValidation
       ExecuteValidation --> StoreValidationResult
       StoreValidationResult --> [*]

       ExecuteValidation --> ValidationFailed: Policy violation
       ValidationFailed --> StoreValidationResult

Activities
~~~~~~~~~~

**fetch_document**
    Retrieve document to validate.

**fetch_policy**
    Get validation policy rules.

**execute_validation**
    Run validation checks.

    Returns validation result with:

    - ``is_valid``: Boolean result
    - ``violations``: List of policy violations
    - ``metadata``: Additional validation info

**store_validation_result**
    Persist validation outcome.

Workflow Monitoring
-------------------

Temporal UI
~~~~~~~~~~~

Access the Temporal UI at http://localhost:8001 to:

- View running workflows
- Inspect workflow history
- Retry failed workflows
- Cancel workflows

Workflow Status
~~~~~~~~~~~~~~~

Check workflow status via API::

    GET /workflows/{workflow_id}/status

Query Workflows
~~~~~~~~~~~~~~~

Workflows can expose queries for inspecting state without completing:

.. code-block:: python

    @workflow.query
    def get_progress(self) -> dict:
        return {
            "step": self.current_step,
            "progress": self.progress_percentage
        }

Best Practices
--------------

Workflow Design
~~~~~~~~~~~~~~~

1. **Deterministic**: Workflows must be deterministic for replay
2. **Idempotent Activities**: Activities should handle retries gracefully
3. **Timeouts**: Set appropriate timeouts for all activities
4. **State Management**: Use workflow state carefully

Activity Design
~~~~~~~~~~~~~~~

1. **Single Responsibility**: Each activity does one thing
2. **Short Duration**: Keep activities focused and quick
3. **Retry-Safe**: Design for automatic retries
4. **Logging**: Log activity execution for debugging

Error Handling
~~~~~~~~~~~~~~

1. **Expected Errors**: Handle business errors explicitly
2. **Transient Failures**: Use retry policies
3. **Fatal Errors**: Fail fast for unrecoverable errors
4. **Compensation**: Implement cleanup for partial failures

Testing Workflows
-----------------

Unit Testing
~~~~~~~~~~~~

Test workflow logic using Temporal's test framework::

    from temporalio.testing import WorkflowEnvironment
    from workflows import ExtractAssembleWorkflow

    async def test_workflow():
        async with WorkflowEnvironment() as env:
            result = await env.client.execute_workflow(
                ExtractAssembleWorkflow.run,
                args=[document_id, spec_id],
                task_queue="test-queue"
            )

            assert result.status == "completed"

Integration Testing
~~~~~~~~~~~~~~~~~~~

Test with real Temporal server and activities:

1. Start test Temporal server
2. Register test workers
3. Execute workflows with test data
4. Verify outcomes

Advanced Topics
---------------

Versioning
~~~~~~~~~~

Temporal supports workflow versioning for safe deployments:

.. code-block:: python

    version = workflow.get_version("feature-name", 1, 2)
    if version == 1:
        # Old behavior
        pass
    else:
        # New behavior
        pass

Child Workflows
~~~~~~~~~~~~~~~

Workflows can start child workflows for modularity::

    result = await workflow.execute_child_workflow(
        ChildWorkflow.run,
        args=[...],
        id=f"child-{parent_id}"
    )

Signals
~~~~~~~

External events can be sent to running workflows::

    @workflow.signal
    async def cancel_processing(self):
        self.should_cancel = True

Timers
~~~~~~

Workflows can wait for specific durations::

    await asyncio.sleep(60)  # Wait 60 seconds

Continue-As-New
~~~~~~~~~~~~~~~

For very long-running workflows, use continue-as-new to manage history size::

    if iteration_count > 1000:
        workflow.continue_as_new(args=[new_state])
