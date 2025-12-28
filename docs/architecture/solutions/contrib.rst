Contrib Modules
===============

Julee ships with contrib modules that demonstrate common patterns.
These are starting points you can use, extend, or replace.

Like Django's contrib apps, Julee provides ready-made components for common needs.

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

:doc:`Workers </architecture/applications/worker>` execute these workflows.

Repository Implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~

Example storage implementations:

**MinIO Repositories**
    S3-compatible object storage.

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

These implement the :doc:`repository pattern </architecture/clean_architecture/repositories>`.

Service Implementations
~~~~~~~~~~~~~~~~~~~~~~~

AI and external service integrations:

**Knowledge Services**
    AI-powered document processing.

    - :py:class:`~julee.services.knowledge_service.anthropic.AnthropicKnowledgeService` - Claude integration
    - ``OpenAIKnowledgeService`` - GPT integration
    - :py:class:`~julee.services.knowledge_service.memory.MemoryKnowledgeService` - Mock for testing

These implement the :doc:`service pattern </architecture/clean_architecture/services>`.

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

Using Contrib Modules
---------------------

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

Extend contrib modules for custom needs:

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

CEAP: An Example Contrib Module
-------------------------------

CEAP (Capture, Extract, Assemble, Publish) is an example contrib module that demonstrates Julee's patterns.

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

Why Include CEAP?
~~~~~~~~~~~~~~~~~

**Common Pattern**
    AI document processing often follows capture-extract-assemble-publish. CEAP demonstrates how to implement this pattern with Julee.

**Reference Implementation**
    Shows how to structure workflows, handle errors, and integrate with Temporal.

**Extensible Starting Point**
    Use CEAP as-is, extend it, or use it as a reference for building your own workflows.

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

Contrib Philosophy
------------------

**Starting Points**
    Contrib modules demonstrate patterns. Start here and customize.

**Consistent Patterns**
    All contrib modules follow Julee's architectural patterns. Learn one, understand all.

**Optional, Not Required**
    Contrib modules are conveniences, not constraints. Replace any component with your own implementation.

What Makes a Good Contrib Module?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contrib modules should be:

**Generic**
    Useful across many solutions, not specific to one domain.

**Well-Tested**
    Include tests and documentation.

**Configurable**
    Adaptable to different environments and requirements.

**Replaceable**
    Behind protocols so you can swap implementations.

Contributing
~~~~~~~~~~~~

If you build a reusable module, consider contributing it back:

1. Ensure it follows Julee's architectural patterns
2. Hide behind protocols for replaceability
3. Include tests and documentation
4. Submit as a PR to the Julee repository
