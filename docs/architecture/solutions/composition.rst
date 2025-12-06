Composition
===========

A **composition** is the fundamental unit of work in Julee: a use case combined with the services and repositories it needs to execute.

::

    Composition = Use Case + Services + Repositories

Compositions represent business operations. They can be executed directly (synchronous, simple) or dispatched as pipelines (reliable, auditable).

What is a Composition?
----------------------

A composition brings together:

**Use Case**
    Domain logic that orchestrates the operation. Defines *what* needs to happen.

**Services**
    External capabilities the use case depends on. AI providers, validation services, notification services.

**Repositories**
    Data access the use case needs. Document storage, configuration storage, result storage.

The use case defines the business logic. Services and repositories are injected via dependency injection, making the composition testable and flexible.

Example Composition
~~~~~~~~~~~~~~~~~~~

::

    class ExtractAssembleComposition:
        """Composition: Extract data from document and assemble results."""

        def __init__(
            self,
            # Repositories (data access)
            document_repo: DocumentRepository,
            spec_repo: AssemblySpecificationRepository,
            assembly_repo: AssemblyRepository,
            # Services (external capabilities)
            knowledge_service: KnowledgeService,
        ):
            self.document_repo = document_repo
            self.spec_repo = spec_repo
            self.assembly_repo = assembly_repo
            self.knowledge_service = knowledge_service

        async def execute(self, document_id: str, spec_id: str) -> Assembly:
            # Fetch inputs
            document = await self.document_repo.get(document_id)
            spec = await self.spec_repo.get(spec_id)

            # Execute AI extraction (via service)
            extracted_data = await self.knowledge_service.query(
                document.file_id,
                spec.extraction_prompt
            )

            # Assemble results (domain logic)
            assembly = Assembly(
                document_id=document_id,
                specification_id=spec_id,
                data=extracted_data
            )

            # Store result
            await self.assembly_repo.create(assembly)

            return assembly

This composition:

- Uses **repositories** to fetch document and specification, store assembly
- Uses **knowledge service** to extract data via AI
- Contains **domain logic** for assembling results
- Has **no knowledge** of how it will be executed (API, CLI, or pipeline)

Direct vs Pipeline Execution
----------------------------

Compositions can be executed two ways:

Direct Execution
~~~~~~~~~~~~~~~~

Run the composition immediately in an API endpoint or CLI command.

::

    # API endpoint - direct execution
    @router.post("/extract")
    async def extract_endpoint(
        document_id: str,
        spec_id: str,
        composition: ExtractAssembleComposition = Depends(get_composition)
    ):
        return await composition.execute(document_id, spec_id)

    # CLI command - direct execution
    @app.command()
    def extract(document_id: str, spec_id: str):
        composition = create_composition()
        result = asyncio.run(composition.execute(document_id, spec_id))
        print(result)

**Characteristics of direct execution:**

- Synchronous from caller's perspective
- No automatic retries on failure
- No audit trail beyond application logs
- No supply chain provenance
- Simple and fast for quick operations

**When to use direct execution:**

- Simple, fast operations
- Operations where failure is acceptable
- Development and testing
- Operations not requiring audit trails

Pipeline Execution
~~~~~~~~~~~~~~~~~~

Dispatch the composition to run as a Temporal workflow (see :py:class:`~julee.workflows.extract_assemble.ExtractAssembleWorkflow`).

::

    # API endpoint - dispatch to pipeline
    @router.post("/extract-async")
    async def extract_async_endpoint(
        document_id: str,
        spec_id: str,
        temporal: Client = Depends(get_temporal_client)
    ):
        handle = await temporal.start_workflow(
            ExtractAssembleWorkflow.run,
            args=[document_id, spec_id],
            id=f"extract-{document_id}",
            task_queue="julee-queue"
        )
        return {"workflow_id": handle.id}

    # CLI command - dispatch to pipeline
    @app.command()
    def extract_async(document_id: str, spec_id: str):
        client = get_temporal_client()
        handle = asyncio.run(
            client.start_workflow(
                ExtractAssembleWorkflow.run,
                args=[document_id, spec_id],
                id=f"extract-{document_id}",
                task_queue="julee-queue"
            )
        )
        print(f"Started pipeline: {handle.id}")

**Characteristics of pipeline execution:**

- Asynchronous - caller gets workflow ID, result comes later
- Automatic retries with configurable policies
- Complete audit trail in Temporal
- Supply chain provenance for every step
- Reliable execution even if services fail temporarily

**When to use pipeline execution:**

- Long-running operations
- Operations involving unreliable services (AI, external APIs)
- Operations requiring audit trails
- Compliance-critical processes
- Operations where failure must be handled gracefully

See :doc:`pipelines` for details on pipeline execution and supply chain provenance.

Wiring Compositions
-------------------

Compositions are wired together using dependency injection.

Factory Functions
~~~~~~~~~~~~~~~~~

Create factory functions that assemble compositions:

::

    # In infrastructure/dependencies.py
    from fastapi import Depends

    def get_extract_assemble_composition(
        document_repo: DocumentRepository = Depends(get_document_repo),
        spec_repo: AssemblySpecificationRepository = Depends(get_spec_repo),
        assembly_repo: AssemblyRepository = Depends(get_assembly_repo),
        knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    ) -> ExtractAssembleComposition:
        return ExtractAssembleComposition(
            document_repo=document_repo,
            spec_repo=spec_repo,
            assembly_repo=assembly_repo,
            knowledge_service=knowledge_service,
        )

Configuration-Based Wiring
~~~~~~~~~~~~~~~~~~~~~~~~~~

Choose implementations based on configuration:

::

    def get_knowledge_service(
        settings: Settings = Depends(get_settings)
    ) -> KnowledgeService:
        if settings.ai_provider == "anthropic":
            return AnthropicKnowledgeService(api_key=settings.anthropic_api_key)
        elif settings.ai_provider == "openai":
            return OpenAIKnowledgeService(api_key=settings.openai_api_key)
        elif settings.ai_provider == "local":
            return LocalLLMService(endpoint=settings.llm_endpoint)
        else:
            raise ValueError(f"Unknown AI provider: {settings.ai_provider}")

See :doc:`/architecture/clean_architecture/protocols` for dependency injection patterns.

Testing Compositions
--------------------

Compositions are highly testable because dependencies are injected.

Unit Testing
~~~~~~~~~~~~

Use in-memory implementations for fast tests:

::

    @pytest.mark.asyncio
    async def test_extract_assemble():
        # Create test implementations
        document_repo = MemoryDocumentRepository()
        spec_repo = MemorySpecificationRepository()
        assembly_repo = MemoryAssemblyRepository()
        knowledge_service = MemoryKnowledgeService()

        # Seed test data
        await document_repo.create(test_document)
        await spec_repo.create(test_spec)

        # Wire composition
        composition = ExtractAssembleComposition(
            document_repo=document_repo,
            spec_repo=spec_repo,
            assembly_repo=assembly_repo,
            knowledge_service=knowledge_service,
        )

        # Execute
        result = await composition.execute("doc-1", "spec-1")

        # Verify
        assert result is not None
        assert result.document_id == "doc-1"

Integration Testing
~~~~~~~~~~~~~~~~~~~

Test with real services:

::

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_extract_assemble_with_real_ai():
        # Real storage, real AI
        composition = ExtractAssembleComposition(
            document_repo=MinioDocumentRepository(test_client),
            spec_repo=MinioSpecificationRepository(test_client),
            assembly_repo=MinioAssemblyRepository(test_client),
            knowledge_service=AnthropicKnowledgeService(api_key=test_api_key),
        )

        result = await composition.execute("doc-1", "spec-1")

        assert result is not None

Composition Patterns
--------------------

Pattern: Composed Compositions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compositions can use other compositions:

::

    class ValidateAndExtractComposition:
        def __init__(
            self,
            validate_composition: ValidateDocumentComposition,
            extract_composition: ExtractAssembleComposition,
        ):
            self.validate = validate_composition
            self.extract = extract_composition

        async def execute(self, document_id: str, spec_id: str, policy_id: str):
            # First validate
            validation = await self.validate.execute(document_id, policy_id)
            if not validation.is_valid:
                raise ValidationError(validation.violations)

            # Then extract
            return await self.extract.execute(document_id, spec_id)

Pattern: Conditional Services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Choose services based on input:

::

    class SmartExtractionComposition:
        def __init__(
            self,
            document_repo: DocumentRepository,
            anthropic_service: KnowledgeService,
            local_service: KnowledgeService,
        ):
            self.document_repo = document_repo
            self.anthropic = anthropic_service
            self.local = local_service

        async def execute(self, document_id: str, use_local: bool = False):
            document = await self.document_repo.get(document_id)

            # Choose service based on input
            service = self.local if use_local else self.anthropic

            return await service.query(document.file_id, "Extract data")

Summary
-------

Compositions combine use cases with services and repositories. The composition doesn't know how it will be executed—applications decide whether to run directly (simple) or dispatch as a :doc:`pipeline <pipelines>` (reliable, auditable).
