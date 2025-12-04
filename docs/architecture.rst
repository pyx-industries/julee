Architecture
============

System Overview
---------------

Julee follows **Clean Architecture** principles with clear separation between layers:

.. mermaid::

   graph LR
       subgraph "Presentation Layer"
           UI[React UI]
           API[FastAPI]
       end

       subgraph "Application Layer"
           UC[Use Cases]
       end

       subgraph "Domain Layer"
           M[Models]
           R[Repository Protocols]
       end

       subgraph "Infrastructure Layer"
           MR[MinIO Repos]
           TR[Temporal Repos]
           KS[Knowledge Services]
       end

       UI --> API
       API --> UC
       UC --> M
       UC --> R
       R -.implements.-> MR
       R -.implements.-> TR
       UC --> KS

Layer Responsibilities
----------------------

Domain Layer
~~~~~~~~~~~~

The core of the application containing:

**Models** (``domain/models/``)
    - Pydantic-based domain entities
    - Type-safe data structures
    - Business validation rules

**Repository Protocols** (``domain/repositories/``)
    - Abstract interfaces for data access
    - Protocol-based design for type safety
    - Implementation-agnostic

**Use Cases** (``domain/use_cases/``)
    - Business logic orchestration
    - Workflow coordination
    - Cross-cutting concerns

Application Layer
~~~~~~~~~~~~~~~~~

**API** (``api/``)
    - FastAPI REST endpoints
    - Request/response models
    - Dependency injection
    - Route handlers

Infrastructure Layer
~~~~~~~~~~~~~~~~~~~~

**Repository Implementations** (``repositories/``)

    - ``minio/``: MinIO-based storage implementations
    - ``memory/``: In-memory implementations for testing
    - ``temporal/``: Temporal activity implementations

**Services** (``services/``)
    - External service integrations
    - Knowledge service implementations
    - Temporal workflow/activity definitions

**Workflows** (``workflows/``)
    - Temporal workflow definitions
    - Long-running business processes

Data Flow
---------

Extraction and Assembly
~~~~~~~~~~~~~~~~~~~~~~~

.. mermaid::

   sequenceDiagram
       participant Client
       participant API
       participant Temporal
       participant Worker
       participant MinIO
       participant KnowledgeService

       Client->>API: POST /workflows/extract-assemble
       API->>Temporal: Start workflow
       Temporal->>Worker: Execute workflow
       Worker->>MinIO: Fetch document
       Worker->>MinIO: Fetch specification
       Worker->>KnowledgeService: Extract data
       KnowledgeService-->>Worker: Extracted data
       Worker->>Worker: Assemble data
       Worker->>MinIO: Store assembly
       Worker-->>Temporal: Complete
       Temporal-->>API: Workflow result
       API-->>Client: Response

Dependency Injection
--------------------

The system uses FastAPI's dependency injection for managing:

- Repository instances
- Temporal client connections
- MinIO client connections
- Configuration

Example::

    @app.get("/documents/{document_id}")
    async def get_document(
        document_id: str,
        repo: DocumentRepository = Depends(get_document_repository)
    ):
        return await repo.get(document_id)

Repository Pattern
------------------

All data access goes through repository interfaces::

    class DocumentRepository(Protocol):
        async def create(self, document: Document) -> Document: ...
        async def get(self, id: str) -> Optional[Document]: ...
        async def update(self, document: Document) -> Document: ...
        async def delete(self, id: str) -> None: ...
        async def list(self) -> List[Document]: ...

Benefits:

- Testability: Easy to mock repositories
- Flexibility: Swap implementations without changing business logic
- Type safety: Protocol-based design with mypy support

Temporal Integration
--------------------

Workflows
~~~~~~~~~

Workflows orchestrate long-running processes:

- Durable execution across failures
- Replay-based recovery
- State management

Activities
~~~~~~~~~~

Activities are individual units of work:

- Repository operations
- External API calls
- Knowledge service queries

Each activity is registered using decorators::

    @temporal_activity_protocol_implementation(DocumentRepository)
    class TemporalMinioDocumentRepository:
        # Implementation with automatic activity registration

Error Handling
--------------

The system implements comprehensive error handling:

1. **Domain Layer**: Business rule validation
2. **Application Layer**: Request validation
3. **Infrastructure Layer**: External service errors
4. **Temporal**: Automatic retry with exponential backoff

Storage Architecture
--------------------

MinIO Buckets
~~~~~~~~~~~~~

Each domain entity has its own bucket:

- Isolation between entity types
- Independent lifecycle management
- Versioning support

Object Keys
~~~~~~~~~~~

Keys follow a hierarchical structure::

    {entity-type}/{entity-id}/{version}.json

This enables:

- Easy listing by entity type
- Version history tracking
- Efficient lookups

Testing Strategy
----------------

**Unit Tests**
    - Test domain models and use cases
    - Use in-memory repository implementations
    - Fast, isolated tests

**Integration Tests**
    - Test with real MinIO instances
    - Verify repository implementations
    - Test API endpoints

**Workflow Tests**
    - Use Temporal test server
    - Verify workflow logic
    - Test activity implementations

Extensibility
-------------

Adding New Entity Types
~~~~~~~~~~~~~~~~~~~~~~~

1. Define domain model in ``domain/models/``
2. Create repository protocol in ``domain/repositories/``
3. Implement repository in ``repositories/minio/``
4. Add API routes in ``api/routers/``
5. Register with dependency injection

Adding New Knowledge Services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Implement ``KnowledgeService`` protocol
2. Add service-specific configuration
3. Update factory to instantiate new service
4. Register in dependency injection

Performance Considerations
--------------------------

**Caching**
    - Repository-level caching can be added
    - Consider Redis for distributed caching

**Streaming**
    - Large documents use streaming APIs
    - Minimize memory footprint

**Concurrency**
    - Async/await throughout
    - FastAPI handles concurrent requests
    - Temporal manages workflow concurrency

Security Considerations
-----------------------

**API Keys**
    - Stored in environment variables
    - Never logged or exposed

**Data Access**
    - Repository pattern controls all data access
    - Easy to add authorization checks

**Network Security**
    - API can be secured with authentication middleware
    - MinIO supports TLS
    - Temporal supports mTLS
