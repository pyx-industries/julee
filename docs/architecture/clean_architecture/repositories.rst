Repositories
============

**Canonical Definition: Repositories store things.**

A repository implements simple CRUD operations for domain entities, abstracting storage technology.

This is the single source of truth for the repository pattern in Julee.

What is a Repository?
---------------------

A repository is responsible for persistence of domain entities.

**Responsibilities:**

- Create (store new entities)
- Read (retrieve entities by ID, list entities)
- Update (modify existing entities)
- Delete (remove entities)

**Not responsibilities:**

- Business logic
- Validation beyond storage constraints
- Complex queries requiring joins or aggregations
- Operations on multiple entity types

**Key distinction:** Repositories handle *persistence only*.

For complex operations beyond storage, see :doc:`services`.

When to Use a Repository
------------------------

Create a repository when you need to:

**Persist Domain Entities**
    Documents, Assemblies, Policies, Specifications - entities defined in your domain.

**Abstract Storage Technology**
    Hide whether you're using S3, PostgreSQL, or in-memory storage.

**Enable Testing**
    Swap real storage for in-memory implementation in tests.

**Support Multiple Backends**
    Same interface, different storage (e.g., MinIO in production, memory in tests).

When NOT to Use a Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Don't create repositories for:**

- Operations that don't persist entities
- Read-only data sources (use a service)
- Complex queries across multiple entities (use a service)
- Transformations or enrichment (use a use case)

The Repository Protocol
-----------------------

**The canonical protocol definition.**

Every repository in Julee follows this pattern::

    from typing import Protocol
    from domain.models import Document

    class DocumentRepository(Protocol):
        """Protocol for document persistence.

        Repositories handle CRUD operations for documents.
        """

        async def create(self, doc: Document) -> Document:
            """Store a new document.

            Args:
                doc: Document to store

            Returns:
                The stored document (may include generated fields)

            Raises:
                ConflictError: If document with same ID already exists
            """
            ...

        async def get(self, id: str) -> Document | None:
            """Retrieve document by ID.

            Args:
                id: Document identifier

            Returns:
                The document if found, None otherwise
            """
            ...

        async def list(self) -> list[Document]:
            """List all documents.

            Returns:
                List of all documents (may be empty)
            """
            ...

        async def update(self, doc: Document) -> Document:
            """Update existing document.

            Args:
                doc: Document with updated fields

            Returns:
                The updated document

            Raises:
                NotFoundError: If document doesn't exist
            """
            ...

        async def delete(self, id: str) -> None:
            """Delete document by ID.

            Args:
                id: Document identifier

            Raises:
                NotFoundError: If document doesn't exist
            """
            ...

**Protocol variations:**

Different repositories may have slightly different methods based on entity needs, but all follow CRUD pattern.

**Example: Assembly Repository**

::

    class AssemblyRepository(Protocol):
        """Protocol for assembly persistence."""

        async def create(self, assembly: Assembly) -> Assembly: ...
        async def get(self, id: str) -> Assembly | None: ...
        async def list(self, document_id: str | None = None) -> list[Assembly]: ...
        async def delete(self, id: str) -> None: ...

Note: ``list`` takes optional ``document_id`` filter. This is acceptable - repositories can have query parameters for simple filtering.

**Example: Policy Repository**

::

    class PolicyRepository(Protocol):
        """Protocol for policy persistence."""

        async def create(self, policy: Policy) -> Policy: ...
        async def get(self, id: str) -> Policy | None: ...
        async def list(self, active_only: bool = False) -> list[Policy]: ...
        async def update(self, policy: Policy) -> Policy: ...
        async def delete(self, id: str) -> None: ...

Note: ``active_only`` flag for simple filtering. Keep query parameters simple.

Repository Implementations
--------------------------

Julee provides three standard implementations:

MinIO Repository (Production)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

S3-compatible object storage for production use::

    from minio import Minio
    from domain.models import Document
    import json

    class MinioDocumentRepository:
        """MinIO implementation of DocumentRepository.

        Stores documents as JSON objects in MinIO buckets.
        """

        def __init__(self, client: Minio, bucket: str = "documents"):
            self.client = client
            self.bucket = bucket

        async def create(self, doc: Document) -> Document:
            """Store document in MinIO."""
            data = doc.model_dump_json()
            await self.client.put_object(
                bucket_name=self.bucket,
                object_name=doc.id,
                data=data.encode('utf-8'),
                length=len(data),
                content_type='application/json'
            )
            return doc

        async def get(self, id: str) -> Document | None:
            """Retrieve document from MinIO."""
            try:
                response = await self.client.get_object(
                    bucket_name=self.bucket,
                    object_name=id
                )
                data = await response.read()
                return Document.model_validate_json(data)
            except Exception:
                return None

        async def list(self) -> list[Document]:
            """List all documents in bucket."""
            objects = await self.client.list_objects(
                bucket_name=self.bucket
            )
            docs = []
            for obj in objects:
                doc = await self.get(obj.object_name)
                if doc:
                    docs.append(doc)
            return docs

        async def update(self, doc: Document) -> Document:
            """Update document (same as create in object storage)."""
            return await self.create(doc)

        async def delete(self, id: str) -> None:
            """Delete document from MinIO."""
            await self.client.remove_object(
                bucket_name=self.bucket,
                object_name=id
            )

**When to use:** Production deployments, when you need durable object storage.

Memory Repository (Testing)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In-memory storage for fast tests::

    from domain.models import Document

    class MemoryDocumentRepository:
        """In-memory implementation of DocumentRepository.

        Stores documents in a dictionary. Fast, but not durable.
        """

        def __init__(self):
            self._documents: dict[str, Document] = {}

        async def create(self, doc: Document) -> Document:
            """Store document in memory."""
            if doc.id in self._documents:
                raise ValueError(f"Document {doc.id} already exists")
            self._documents[doc.id] = doc
            return doc

        async def get(self, id: str) -> Document | None:
            """Retrieve document from memory."""
            return self._documents.get(id)

        async def list(self) -> list[Document]:
            """List all documents in memory."""
            return list(self._documents.values())

        async def update(self, doc: Document) -> Document:
            """Update document in memory."""
            if doc.id not in self._documents:
                raise ValueError(f"Document {doc.id} not found")
            self._documents[doc.id] = doc
            return doc

        async def delete(self, id: str) -> None:
            """Delete document from memory."""
            self._documents.pop(id, None)

**When to use:** Unit tests, local development, CI/CD pipelines.

PostgreSQL Repository (Relational)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Relational database storage for complex queries::

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from domain.models import Document
    from infrastructure.db.models import DocumentModel

    class PostgreSQLDocumentRepository:
        """PostgreSQL implementation of DocumentRepository.

        Uses SQLAlchemy for ORM access.
        """

        def __init__(self, session: AsyncSession):
            self.session = session

        async def create(self, doc: Document) -> Document:
            """Store document in PostgreSQL."""
            db_doc = DocumentModel(
                id=doc.id,
                name=doc.name,
                content=doc.content,
                content_type=doc.content_type,
                created_at=doc.created_at
            )
            self.session.add(db_doc)
            await self.session.commit()
            return doc

        async def get(self, id: str) -> Document | None:
            """Retrieve document from PostgreSQL."""
            result = await self.session.execute(
                select(DocumentModel).where(DocumentModel.id == id)
            )
            db_doc = result.scalar_one_or_none()
            if not db_doc:
                return None

            return Document(
                id=db_doc.id,
                name=db_doc.name,
                content=db_doc.content,
                content_type=db_doc.content_type,
                created_at=db_doc.created_at
            )

        async def list(self) -> list[Document]:
            """List all documents from PostgreSQL."""
            result = await self.session.execute(
                select(DocumentModel).order_by(DocumentModel.created_at.desc())
            )
            db_docs = result.scalars().all()

            return [
                Document(
                    id=db_doc.id,
                    name=db_doc.name,
                    content=db_doc.content,
                    content_type=db_doc.content_type,
                    created_at=db_doc.created_at
                )
                for db_doc in db_docs
            ]

        async def update(self, doc: Document) -> Document:
            """Update document in PostgreSQL."""
            result = await self.session.execute(
                select(DocumentModel).where(DocumentModel.id == doc.id)
            )
            db_doc = result.scalar_one_or_none()
            if not db_doc:
                raise ValueError(f"Document {doc.id} not found")

            db_doc.name = doc.name
            db_doc.content = doc.content
            await self.session.commit()
            return doc

        async def delete(self, id: str) -> None:
            """Delete document from PostgreSQL."""
            result = await self.session.execute(
                select(DocumentModel).where(DocumentModel.id == id)
            )
            db_doc = result.scalar_one_or_none()
            if db_doc:
                await self.session.delete(db_doc)
                await self.session.commit()

**When to use:** When you need relational queries, transactions, or complex filtering.

Using Repositories
------------------

In Use Cases
~~~~~~~~~~~~

Use cases depend on repository protocols::

    from domain.repositories.document import DocumentRepository
    from domain.repositories.assembly import AssemblyRepository

    class ExtractAssembleUseCase:
        def __init__(
            self,
            doc_repo: DocumentRepository,
            assembly_repo: AssemblyRepository
        ):
            self.doc_repo = doc_repo
            self.assembly_repo = assembly_repo

        async def execute(self, doc_id: str) -> Assembly:
            # Retrieve document
            doc = await self.doc_repo.get(doc_id)
            if not doc:
                raise ValueError(f"Document {doc_id} not found")

            # Process document
            result = await self.process(doc)

            # Store assembly
            assembly = Assembly(
                id=generate_id(),
                document_id=doc_id,
                data=result
            )
            await self.assembly_repo.create(assembly)

            return assembly

The use case has no knowledge of storage technology.

In API Endpoints
~~~~~~~~~~~~~~~~

Inject repositories via dependency injection::

    from fastapi import APIRouter, Depends
    from domain.repositories.document import DocumentRepository
    from infrastructure.dependencies import get_document_repository

    router = APIRouter()

    @router.post("/documents")
    async def create_document(
        doc: Document,
        repo: DocumentRepository = Depends(get_document_repository)
    ) -> Document:
        """Create a new document."""
        return await repo.create(doc)

    @router.get("/documents/{doc_id}")
    async def get_document(
        doc_id: str,
        repo: DocumentRepository = Depends(get_document_repository)
    ) -> Document:
        """Retrieve a document."""
        doc = await repo.get(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

See :doc:`protocols` for dependency injection details.

Testing with Repositories
--------------------------

Unit Tests
~~~~~~~~~~

Use in-memory repositories for fast tests::

    import pytest
    from infrastructure.repositories.memory_document import MemoryDocumentRepository
    from domain.models import Document

    @pytest.mark.asyncio
    async def test_create_and_retrieve():
        # Use in-memory repository
        repo = MemoryDocumentRepository()

        # Create document
        doc = Document(
            id="test-1",
            name="Test Document",
            content=b"test content"
        )
        await repo.create(doc)

        # Retrieve document
        retrieved = await repo.get("test-1")

        # Verify
        assert retrieved is not None
        assert retrieved.id == "test-1"
        assert retrieved.name == "Test Document"

**Benefits:**

- No external dependencies
- Fast execution (microseconds)
- Deterministic results

Integration Tests
~~~~~~~~~~~~~~~~~

Use real repositories to test storage logic::

    import pytest
    from infrastructure.repositories.minio_document import MinioDocumentRepository
    from domain.models import Document

    @pytest.mark.asyncio
    async def test_minio_persistence():
        # Use real MinIO (test instance)
        client = get_test_minio_client()
        repo = MinioDocumentRepository(client, bucket="test-documents")

        # Create document
        doc = Document(id="test-1", name="Test", content=b"content")
        await repo.create(doc)

        # Verify storage
        retrieved = await repo.get("test-1")
        assert retrieved is not None

        # Cleanup
        await repo.delete("test-1")

**Benefits:**

- Verifies actual storage behavior
- Tests serialization/deserialization
- Catches storage-specific issues

Common Patterns
---------------

Pattern: List with Filter
~~~~~~~~~~~~~~~~~~~~~~~~~~

Simple filtering in list method::

    class AssemblyRepository(Protocol):
        async def list(
            self,
            document_id: str | None = None,
            status: str | None = None
        ) -> list[Assembly]:
            """List assemblies with optional filters."""
            ...

Implementation::

    class MemoryAssemblyRepository:
        async def list(
            self,
            document_id: str | None = None,
            status: str | None = None
        ) -> list[Assembly]:
            """List with filtering."""
            assemblies = list(self._assemblies.values())

            if document_id:
                assemblies = [
                    a for a in assemblies
                    if a.document_id == document_id
                ]

            if status:
                assemblies = [
                    a for a in assemblies
                    if a.status == status
                ]

            return assemblies

Pattern: Batch Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~

When you need to create/update multiple entities::

    class DocumentRepository(Protocol):
        async def create_batch(self, docs: list[Document]) -> list[Document]:
            """Create multiple documents efficiently."""
            ...

        async def get_batch(self, ids: list[str]) -> list[Document]:
            """Retrieve multiple documents."""
            ...

Pattern: Exists Check
~~~~~~~~~~~~~~~~~~~~~

Lightweight check without full retrieval::

    class DocumentRepository(Protocol):
        async def exists(self, id: str) -> bool:
            """Check if document exists."""
            ...

Implementation::

    class MinioDocumentRepository:
        async def exists(self, id: str) -> bool:
            """Check existence in MinIO."""
            try:
                await self.client.stat_object(
                    bucket_name=self.bucket,
                    object_name=id
                )
                return True
            except:
                return False

Common Mistakes
---------------

Mistake 1: Business Logic in Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Wrong:**

::

    class DocumentRepository:
        async def create(self, doc: Document) -> Document:
            # Validation in repository ❌
            if not doc.name:
                raise ValueError("Name required")

            # Business rule in repository ❌
            if doc.size > MAX_SIZE:
                raise ValueError("Document too large")

            await self.store(doc)

**Right:**

::

    # Domain model validates ✓
    class Document(BaseModel):
        name: str = Field(min_length=1)  # Validation here
        size: int

    # Use case enforces business rules ✓
    class CreateDocumentUseCase:
        async def execute(self, doc: Document):
            if doc.size > MAX_SIZE:
                raise ValueError("Document too large")

            await self.repo.create(doc)

    # Repository just stores ✓
    class DocumentRepository:
        async def create(self, doc: Document) -> Document:
            await self.store(doc)

Mistake 2: Complex Queries in Repository Protocol
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Wrong:**

::

    class DocumentRepository(Protocol):
        # Too complex for repository ❌
        async def find_documents_by_author_and_date_range_with_tags(
            self,
            author_id: str,
            start_date: datetime,
            end_date: datetime,
            tags: list[str]
        ) -> list[Document]:
            ...

**Right:**

::

    # Simple repository ✓
    class DocumentRepository(Protocol):
        async def list(self) -> list[Document]: ...

    # Complex query in service ✓
    class DocumentQueryService:
        async def find_by_criteria(
            self,
            author_id: str,
            start_date: datetime,
            end_date: datetime,
            tags: list[str]
        ) -> list[Document]:
            docs = await self.repo.list()
            # Filter in service
            return [
                doc for doc in docs
                if (doc.author_id == author_id and
                    start_date <= doc.created_at <= end_date and
                    any(tag in doc.tags for tag in tags))
            ]

Mistake 3: Repository Calling Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Wrong:**

::

    class AssemblyRepository:
        def __init__(self, doc_repo: DocumentRepository):
            self.doc_repo = doc_repo

        async def create(self, assembly: Assembly) -> Assembly:
            # Repository calling repository ❌
            doc = await self.doc_repo.get(assembly.document_id)
            if not doc:
                raise ValueError("Document not found")

            await self.store(assembly)

**Right:**

::

    # Repository just stores ✓
    class AssemblyRepository:
        async def create(self, assembly: Assembly) -> Assembly:
            await self.store(assembly)

    # Use case coordinates ✓
    class CreateAssemblyUseCase:
        def __init__(
            self,
            doc_repo: DocumentRepository,
            assembly_repo: AssemblyRepository
        ):
            self.doc_repo = doc_repo
            self.assembly_repo = assembly_repo

        async def execute(self, assembly: Assembly):
            # Use case checks document exists
            doc = await self.doc_repo.get(assembly.document_id)
            if not doc:
                raise ValueError("Document not found")

            # Use case creates assembly
            await self.assembly_repo.create(assembly)

Summary
-------

**Repositories store things.**

Key principles:

**CRUD Operations Only**
    Create, Read, Update, Delete. Keep it simple.

**Protocol-Based**
    Domain defines protocol, infrastructure implements.

**No Business Logic**
    Repositories persist, use cases orchestrate.

**Multiple Implementations**
    MinIO for production, memory for testing, PostgreSQL for queries.

**Dependency Injection**
    Wire implementations at runtime.

For the service pattern, see :doc:`services`.

For dependency injection, see :doc:`protocols`.

For layer organization, see :doc:`index`.
