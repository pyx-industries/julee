Protocols
=========

Protocol-based design is how Julee achieves flexibility, testability, and maintainability in AI systems.

This page defines the protocol pattern and dependency injection - **the canonical reference**.

What is Protocol-Based Design?
-------------------------------

**Protocols define interfaces without implementation.**

In Python, a protocol is a structural type - any class that implements the required methods satisfies the protocol.

**Why protocols instead of inheritance:**

- **Flexibility** - Multiple implementations without coupling
- **Testability** - Easy to mock for tests
- **Type Safety** - Full mypy and IDE support
- **Documentation** - Protocols declare system capabilities explicitly

Protocol Example
~~~~~~~~~~~~~~~~

::

    from typing import Protocol

    class KnowledgeService(Protocol):
        """Protocol for AI knowledge extraction services."""

        async def register_file(self, content: bytes, content_type: str) -> str:
            """Register content, returns file ID."""
            ...

        async def query(self, file_id: str, prompt: str) -> dict:
            """Query with prompt, returns structured data."""
            ...

Any class with these methods satisfies the protocol::

    class AnthropicKnowledgeService:
        """Implements KnowledgeService protocol."""

        async def register_file(self, content: bytes, content_type: str) -> str:
            # Call Anthropic API
            ...

        async def query(self, file_id: str, prompt: str) -> dict:
            # Use Claude
            ...

    class MemoryKnowledgeService:
        """Implements KnowledgeService protocol."""

        async def register_file(self, content: bytes, content_type: str) -> str:
            return "mock-file-id"

        async def query(self, file_id: str, prompt: str) -> dict:
            return {"mocked": "data"}

Both satisfy ``KnowledgeService``. Type checkers verify compatibility.

The Canonical Protocol Pattern
-------------------------------

**Step 1: Domain Defines Protocol**

The domain layer defines what it needs::

    # In domain/repositories/document.py
    from typing import Protocol
    from domain.models import Document

    class DocumentRepository(Protocol):
        """Protocol for document persistence."""

        async def create(self, doc: Document) -> Document:
            """Store new document."""
            ...

        async def get(self, id: str) -> Document | None:
            """Retrieve document by ID."""
            ...

        async def list(self) -> list[Document]:
            """List all documents."""
            ...

        async def delete(self, id: str) -> None:
            """Delete document."""
            ...

**Step 2: Infrastructure Implements Protocol**

Infrastructure provides concrete implementations::

    # In infrastructure/repositories/minio_document.py
    from minio import Minio
    from domain.models import Document

    class MinioDocumentRepository:
        """MinIO implementation of DocumentRepository protocol."""

        def __init__(self, client: Minio):
            self.client = client
            self.bucket = "documents"

        async def create(self, doc: Document) -> Document:
            # Store in MinIO
            await self.client.put_object(
                self.bucket,
                doc.id,
                doc.model_dump_json()
            )
            return doc

        async def get(self, id: str) -> Document | None:
            try:
                data = await self.client.get_object(self.bucket, id)
                return Document.model_validate_json(data)
            except:
                return None

        async def list(self) -> list[Document]:
            objects = await self.client.list_objects(self.bucket)
            return [await self.get(obj.name) for obj in objects]

        async def delete(self, id: str) -> None:
            await self.client.remove_object(self.bucket, id)

Multiple implementations::

    # In infrastructure/repositories/memory_document.py
    from domain.models import Document

    class MemoryDocumentRepository:
        """In-memory implementation for testing."""

        def __init__(self):
            self.documents: dict[str, Document] = {}

        async def create(self, doc: Document) -> Document:
            self.documents[doc.id] = doc
            return doc

        async def get(self, id: str) -> Document | None:
            return self.documents.get(id)

        async def list(self) -> list[Document]:
            return list(self.documents.values())

        async def delete(self, id: str) -> None:
            self.documents.pop(id, None)

Both implement ``DocumentRepository`` protocol.

**Step 3: Domain Uses Protocol**

Use cases depend on protocols, not implementations::

    # In domain/use_cases/extract_assemble.py
    from domain.repositories.document import DocumentRepository
    from domain.services.knowledge import KnowledgeService

    class ExtractAssembleUseCase:
        def __init__(
            self,
            doc_repo: DocumentRepository,        # Protocol type
            knowledge: KnowledgeService           # Protocol type
        ):
            self.doc_repo = doc_repo
            self.knowledge = knowledge

        async def execute(self, doc_id: str) -> dict:
            # Use protocol methods
            doc = await self.doc_repo.get(doc_id)
            if not doc:
                raise ValueError(f"Document {doc_id} not found")

            result = await self.knowledge.query(
                doc.file_id,
                "Extract key information"
            )

            return result

The use case has **zero knowledge** of MinIO, Anthropic, or any concrete implementation.

**Step 4: Dependency Injection Wires It Up**

See `Dependency Injection`_ below.

Dependency Injection
--------------------

**Dependency injection (DI) provides implementations at runtime.**

Julee uses FastAPI's dependency injection system.

The Canonical DI Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~

**Step 1: Create Factory Functions**

Factories instantiate implementations::

    # In infrastructure/dependencies.py
    from fastapi import Depends
    from minio import Minio
    from anthropic import Anthropic
    from config import Settings

    from infrastructure.repositories.minio_document import MinioDocumentRepository
    from infrastructure.services.anthropic_knowledge import AnthropicKnowledgeService

    def get_settings() -> Settings:
        """Load configuration."""
        return Settings()

    def get_minio_client(settings: Settings = Depends(get_settings)) -> Minio:
        """Create MinIO client."""
        return Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False
        )

    def get_document_repository(
        client: Minio = Depends(get_minio_client)
    ) -> DocumentRepository:
        """Create document repository."""
        return MinioDocumentRepository(client)

    def get_knowledge_service(
        settings: Settings = Depends(get_settings)
    ) -> KnowledgeService:
        """Create knowledge service."""
        return AnthropicKnowledgeService(
            api_key=settings.anthropic_api_key
        )

**Step 2: Inject into Use Cases**

Use cases receive dependencies::

    # In API endpoint or activity
    from fastapi import Depends
    from domain.use_cases.extract_assemble import ExtractAssembleUseCase
    from infrastructure.dependencies import (
        get_document_repository,
        get_knowledge_service
    )

    async def extract_data(
        doc_id: str,
        doc_repo: DocumentRepository = Depends(get_document_repository),
        knowledge: KnowledgeService = Depends(get_knowledge_service)
    ) -> dict:
        """Extract data from document."""
        use_case = ExtractAssembleUseCase(
            doc_repo=doc_repo,
            knowledge=knowledge
        )
        return await use_case.execute(doc_id)

**What happens:**

1. FastAPI calls ``get_document_repository()``
2. Which calls ``get_minio_client()``
3. Which calls ``get_settings()``
4. MinIO client created
5. ``MinioDocumentRepository`` created with client
6. ``AnthropicKnowledgeService`` created
7. Both injected into ``extract_data``

**Benefits:**

- Use case doesn't know about MinIO or Anthropic
- Swap implementations by changing factory
- Test with different implementations
- Configuration centralized

Configuration-Based Injection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Choose implementations based on configuration::

    def get_knowledge_service(
        settings: Settings = Depends(get_settings)
    ) -> KnowledgeService:
        """Create knowledge service based on config."""

        if settings.ai_provider == "anthropic":
            return AnthropicKnowledgeService(
                api_key=settings.anthropic_api_key
            )
        elif settings.ai_provider == "openai":
            return OpenAIKnowledgeService(
                api_key=settings.openai_api_key
            )
        elif settings.ai_provider == "local":
            return LocalLLMService(
                endpoint=settings.llm_endpoint
            )
        else:
            raise ValueError(f"Unknown AI provider: {settings.ai_provider}")

Change AI provider with environment variable:

.. code-block:: bash

    AI_PROVIDER=anthropic  # Use Anthropic
    AI_PROVIDER=openai     # Use OpenAI
    AI_PROVIDER=local      # Use local LLM

No code changes needed.

Testing with Protocols
----------------------

Protocols make testing straightforward.

Unit Testing
~~~~~~~~~~~~

Test use cases with fast in-memory implementations::

    import pytest
    from domain.use_cases.extract_assemble import ExtractAssembleUseCase
    from infrastructure.repositories.memory_document import MemoryDocumentRepository
    from infrastructure.services.memory_knowledge import MemoryKnowledgeService
    from domain.models import Document

    @pytest.mark.asyncio
    async def test_extract_assemble():
        # Create test implementations
        doc_repo = MemoryDocumentRepository()
        knowledge = MemoryKnowledgeService()

        # Seed test data
        test_doc = Document(
            id="test-1",
            name="Test Document",
            file_id="file-123"
        )
        await doc_repo.create(test_doc)

        # Create use case with test dependencies
        use_case = ExtractAssembleUseCase(
            doc_repo=doc_repo,
            knowledge=knowledge
        )

        # Test business logic
        result = await use_case.execute("test-1")

        # Verify
        assert result is not None
        assert "mocked" in result

**Benefits:**

- No external dependencies (no MinIO, no AI APIs)
- Fast execution (milliseconds)
- Deterministic results
- Easy to set up test scenarios

Integration Testing
~~~~~~~~~~~~~~~~~~~

Test with real infrastructure::

    @pytest.mark.asyncio
    async def test_with_real_storage():
        # Use real MinIO
        client = get_test_minio_client()
        doc_repo = MinioDocumentRepository(client)

        # But mock expensive AI service
        knowledge = MemoryKnowledgeService()

        # Test with real storage, mock AI
        use_case = ExtractAssembleUseCase(
            doc_repo=doc_repo,
            knowledge=knowledge
        )

        result = await use_case.execute("test-1")

        # Verify actual storage occurred
        stored = await doc_repo.get("test-1")
        assert stored is not None

**Mix and match:**

- Real storage + mock AI (test storage logic)
- Mock storage + real AI (test AI integration)
- All real (end-to-end test)

Mock Implementations
~~~~~~~~~~~~~~~~~~~~

Create custom mocks for specific test scenarios::

    class ErrorKnowledgeService:
        """Mock that always fails - test error handling."""

        async def register_file(self, content: bytes, content_type: str) -> str:
            return "file-id"

        async def query(self, file_id: str, prompt: str) -> dict:
            raise ValueError("AI service unavailable")

    @pytest.mark.asyncio
    async def test_handles_ai_failure():
        doc_repo = MemoryDocumentRepository()
        knowledge = ErrorKnowledgeService()  # Always fails

        use_case = ExtractAssembleUseCase(
            doc_repo=doc_repo,
            knowledge=knowledge
        )

        # Verify error handling
        with pytest.raises(ValueError, match="AI service unavailable"):
            await use_case.execute("test-1")

Benefits of Protocol-Based Design
----------------------------------

Flexibility
~~~~~~~~~~~

Swap implementations without changing use cases:

- Start with Anthropic, switch to OpenAI later
- Compare multiple AI providers side-by-side
- Use local LLM for development, cloud for production

**How:** Change factory function or configuration.

Testability
~~~~~~~~~~~

Test business logic independently:

- Unit tests with in-memory mocks (fast, deterministic)
- Integration tests with real infrastructure (thorough)
- Custom mocks for edge cases (error conditions)

**How:** Inject test implementations via DI.

Type Safety
~~~~~~~~~~~

Catch errors at development time:

- mypy verifies protocol compatibility
- IDE autocomplete shows protocol methods
- Type errors caught before runtime

**How:** Protocol type hints throughout codebase.

Maintainability
~~~~~~~~~~~~~~~

Changes stay localized:

- Add new AI provider? Create new service implementation.
- Change storage backend? Create new repository implementation.
- No changes to domain or use cases required.

**How:** Protocol abstractions isolate concerns.

Documentation
~~~~~~~~~~~~~

Protocols document system capabilities:

- What operations are available?
- What are the contracts?
- What can be swapped?

**How:** Read protocol definitions in domain layer.

Common Patterns
---------------

Pattern: Service Factory
~~~~~~~~~~~~~~~~~~~~~~~~~

When multiple services have similar setup::

    from typing import TypeVar, Type

    ServiceT = TypeVar('ServiceT')

    def create_service(
        service_class: Type[ServiceT],
        settings: Settings
    ) -> ServiceT:
        """Generic service factory."""
        return service_class(
            api_key=settings.get_api_key(service_class),
            timeout=settings.service_timeout,
            retry_count=settings.service_retries
        )

Pattern: Repository Pool
~~~~~~~~~~~~~~~~~~~~~~~~~

When you need multiple repository instances::

    class RepositoryPool:
        """Pool of repository instances."""

        def __init__(self, client: Minio):
            self._client = client
            self._repos: dict[str, DocumentRepository] = {}

        def get_repo(self, bucket: str) -> DocumentRepository:
            """Get or create repository for bucket."""
            if bucket not in self._repos:
                repo = MinioDocumentRepository(self._client)
                repo.bucket = bucket
                self._repos[bucket] = repo
            return self._repos[bucket]

Pattern: Conditional Protocol
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When implementation depends on input::

    class DocumentService:
        def __init__(
            self,
            pdf_parser: PDFParser,
            docx_parser: DOCXParser
        ):
            self.pdf_parser = pdf_parser
            self.docx_parser = docx_parser

        async def parse(self, doc: Document) -> ParsedContent:
            """Choose parser based on document type."""
            if doc.content_type == "application/pdf":
                return await self.pdf_parser.parse(doc.content)
            elif doc.content_type.startswith("application/vnd.openxmlformats"):
                return await self.docx_parser.parse(doc.content)
            else:
                raise ValueError(f"Unsupported type: {doc.content_type}")

Summary
-------

Protocol-based design enables:

**Flexibility**
    Swap implementations via configuration

**Testability**
    Fast unit tests with mocks

**Type Safety**
    Catch errors at development time

**Maintainability**
    Changes stay localized

**Documentation**
    Protocols declare system capabilities

**The pattern:**

1. Domain defines protocol
2. Infrastructure implements protocol
3. Domain uses protocol (not implementation)
4. Dependency injection wires implementations at runtime

For repository protocols, see :doc:`repositories`.

For service protocols, see :doc:`services`.

For layer organization, see :doc:`layers`.
