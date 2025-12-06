Batteries Included
==================

Julee's "batteries included" philosophy means production-ready modules ship with the framework. You can use them immediately without building everything from scratch.

Like Django's admin interface and ORM, Julee provides ready-made components for common needs.

What's Included
---------------

CEAP Workflows
~~~~~~~~~~~~~~

The **Capture, Extract, Assemble, Publish** pattern implemented as Temporal workflows.

:py:class:`~julee.workflows.extract_assemble.ExtractAssembleWorkflow`
    Process documents through AI extraction and assembly.

    - Capture documents from storage
    - Extract structured data using AI services
    - Assemble results according to specifications
    - Publish to storage

:py:class:`~julee.workflows.validate_document.ValidateDocumentWorkflow`
    Validate documents against policies.

    - Fetch document and policy
    - Execute validation rules
    - Record validation results for audit

See :doc:`/architecture/applications/worker` for workflow details.

Repository Implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~

Ready-to-use storage implementations:

**MinIO Repositories**
    S3-compatible object storage for production.

    - :py:class:`~julee.repositories.minio.MinioDocumentRepository`
    - ``MinioAssemblyRepository``
    - ``MinioSpecificationRepository``
    - ``MinioPolicyRepository``

**Memory Repositories**
    In-memory storage for testing and development.

    - :py:class:`~julee.repositories.memory.MemoryDocumentRepository`
    - ``MemoryAssemblyRepository``
    - ``MemorySpecificationRepository``
    - ``MemoryPolicyRepository``

See :doc:`/architecture/clean_architecture/repositories` for repository patterns.

Service Implementations
~~~~~~~~~~~~~~~~~~~~~~~

AI and external service integrations:

**Knowledge Services**
    AI-powered document processing.

    - :py:class:`~julee.services.knowledge_service.anthropic.AnthropicKnowledgeService` - Claude integration
    - ``OpenAIKnowledgeService`` - GPT integration
    - :py:class:`~julee.services.knowledge_service.memory.MemoryKnowledgeService` - Mock for testing

See :doc:`/architecture/clean_architecture/services` for service patterns.

Domain Models
~~~~~~~~~~~~~

Pydantic models for common entities:

- :py:class:`~julee.domain.models.Document` - Content to be processed
- :py:class:`~julee.domain.models.Assembly` - Assembled results
- :py:class:`~julee.domain.models.AssemblySpecification` - Instructions for assembly
- :py:class:`~julee.domain.models.Policy` - Validation and compliance rules
- :py:class:`~julee.domain.models.KnowledgeServiceConfig` - AI service configuration

Temporal Utilities
~~~~~~~~~~~~~~~~~~

Helpers for Temporal integration:

- Activity decorators for automatic registration
- Workflow proxy generators
- Data converters for Pydantic models
- Testing utilities

Using Batteries-Included Modules
--------------------------------

Direct Usage
~~~~~~~~~~~~

Import and use directly:

::

    from julee.workflows import ExtractAssembleWorkflow
    from julee.repositories.minio import MinioDocumentRepository
    from julee.services.knowledge_service.anthropic import AnthropicKnowledgeService

    # Use as-is
    workflow = ExtractAssembleWorkflow
    document_repo = MinioDocumentRepository(minio_client)
    knowledge_service = AnthropicKnowledgeService(api_key)

Configuration
~~~~~~~~~~~~~

Configure via environment or settings:

::

    # Environment variables
    MINIO_ENDPOINT=minio:9000
    MINIO_ACCESS_KEY=minioadmin
    MINIO_SECRET_KEY=minioadmin
    ANTHROPIC_API_KEY=sk-...

    # In code
    from julee.config import Settings

    settings = Settings()
    knowledge_service = AnthropicKnowledgeService(
        api_key=settings.anthropic_api_key,
        model=settings.anthropic_model
    )

Extension
~~~~~~~~~

Extend batteries-included modules for custom needs:

::

    from julee.workflows import ExtractAssembleWorkflow
    from temporalio import workflow

    @workflow.defn
    class CustomExtractWorkflow(ExtractAssembleWorkflow):
        """Extended extraction with custom pre-processing."""

        @workflow.run
        async def run(self, document_id: str, spec_id: str):
            # Custom pre-processing
            await self.preprocess(document_id)

            # Call parent workflow
            result = await super().run(document_id, spec_id)

            # Custom post-processing
            await self.notify_completion(result)

            return result

Replacement
~~~~~~~~~~~

Replace with your own implementations:

::

    from julee.domain.repositories import DocumentRepository

    class MyCustomDocumentRepository:
        """Custom repository implementation."""

        async def create(self, doc: Document) -> Document:
            # Your custom storage logic
            ...

        async def get(self, id: str) -> Document | None:
            # Your custom retrieval logic
            ...

    # Wire in via DI
    def get_document_repository() -> DocumentRepository:
        return MyCustomDocumentRepository()

CEAP: The Core Battery
----------------------

CEAP (Capture, Extract, Assemble, Publish) is Julee's signature batteries-included module.

The CEAP Pattern
~~~~~~~~~~~~~~~~

**Capture**
    Ingest documents into the system. Documents enter as files, PDFs, images, text.

**Extract**
    Use AI/knowledge services to extract structured data. LLMs read and understand content.

**Assemble**
    Combine extracted data according to specifications. Structure raw AI output into domain models.

**Publish**
    Output the assembled content. Store results, trigger downstream processes.

Why CEAP is a Battery
~~~~~~~~~~~~~~~~~~~~~

CEAP ships ready-to-use because:

**Common Pattern**
    Most AI document processing follows capture-extract-assemble-publish. Rather than every solution implementing this, Julee provides it.

**Complex to Build**
    Reliable AI workflows with proper error handling, retries, and audit trails require significant engineering. CEAP handles this complexity.

**Best Practices Built-In**
    Timeout handling, retry policies, activity separation - all based on production experience.

**Extensible Foundation**
    Use CEAP as-is, or extend it for custom needs. The pattern is a starting point, not a constraint.

Using CEAP
~~~~~~~~~~

::

    from temporalio.client import Client
    from julee.workflows import ExtractAssembleWorkflow

    # Start CEAP workflow
    client = await Client.connect("localhost:7233")

    result = await client.execute_workflow(
        ExtractAssembleWorkflow.run,
        args=[document_id, specification_id],
        id=f"extract-{document_id}",
        task_queue="julee-extract-queue"
    )

Or via API:

::

    POST /workflows/extract-assemble
    {
        "document_id": "doc-123",
        "specification_id": "spec-456"
    }

Battery Philosophy
------------------

Why Batteries Included?
~~~~~~~~~~~~~~~~~~~~~~~

**Reduce Time to Value**
    Start with working components. Customize later.

**Encode Best Practices**
    Batteries reflect production-learned patterns. Use them to avoid common mistakes.

**Consistent Patterns**
    All batteries follow Julee's architectural patterns. Learn one, understand all.

**Optional, Not Required**
    Batteries are conveniences, not constraints. Replace any component with your own implementation.

What Makes a Good Battery?
~~~~~~~~~~~~~~~~~~~~~~~~~~

Batteries-included modules should be:

**Generic**
    Useful across many solutions, not specific to one domain.

**Production-Ready**
    Tested, documented, with proper error handling.

**Configurable**
    Adaptable to different environments and requirements.

**Replaceable**
    Behind protocols so you can swap implementations.

Contributing Batteries
~~~~~~~~~~~~~~~~~~~~~~

If you build a reusable module, consider contributing it back:

1. Ensure it follows Julee's architectural patterns
2. Hide behind protocols for replaceability
3. Include tests and documentation
4. Submit as a PR to the Julee repository

See :doc:`/contributing` for contribution guidelines.

Summary
-------

Batteries included: CEAP workflows, repository implementations (MinIO, Memory), service implementations (Anthropic, OpenAI, Mock). Use as-is, configure, extend, or replace with your own implementations.
