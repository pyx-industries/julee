API Applications
================

.. note::
   This page is a stub. Content to be developed.

API applications expose Julee use cases via REST endpoints.

Overview
--------

API applications:

- Execute use cases directly for synchronous operations
- Trigger workflows via Temporal client for async operations
- Handle authentication and authorization
- Transform requests/responses

Julee's API applications use FastAPI with dependency injection.

Key Concepts
------------

**Dependency Injection**
    Use cases receive dependencies (repositories, services) via FastAPI's ``Depends``.

**Request/Response Models**
    Pydantic models for API contracts, separate from domain models.

**Async Operations**
    For long-running operations, trigger Temporal workflows and return workflow ID.

Example
-------

::

    from fastapi import APIRouter, Depends
    from julee.domain.use_cases import ExtractAssembleUseCase
    from infrastructure.dependencies import get_use_case

    router = APIRouter()

    @router.post("/documents/{doc_id}/extract")
    async def extract_document(
        doc_id: str,
        spec_id: str,
        use_case: ExtractAssembleUseCase = Depends(get_use_case)
    ):
        """Synchronous extraction for small documents."""
        return await use_case.execute(doc_id, spec_id)

    @router.post("/documents/{doc_id}/extract-async")
    async def extract_document_async(
        doc_id: str,
        spec_id: str,
        temporal: Client = Depends(get_temporal_client)
    ):
        """Async extraction via Temporal workflow."""
        handle = await temporal.start_workflow(
            ExtractAssembleWorkflow.run,
            args=[doc_id, spec_id],
            id=f"extract-{doc_id}",
            task_queue="julee-queue"
        )
        return {"workflow_id": handle.id}

See Also
--------

- :doc:`/architecture/clean_architecture/protocols` for dependency injection
- :doc:`worker` for async workflow execution
- :doc:`/architecture/deployment` for deployment patterns
