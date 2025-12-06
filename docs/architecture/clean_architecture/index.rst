Clean Architecture
==================

Julee organizes code into three architectural layers: **Domain**, **Application**, and **Infrastructure**.

This separation makes AI systems manageable by isolating concerns and controlling dependencies.

.. toctree::
   :maxdepth: 1
   :caption: Topics

   protocols
   repositories
   services

The Dependency Rule
-------------------

**Dependencies point inward toward the domain.**

The core principle: Outer layers depend on inner layers. Inner layers never depend on outer layers.

.. uml:: ../diagrams/clean_architecture_layers.puml

This means:

- Domain defines ``KnowledgeService`` protocol
- Infrastructure provides ``AnthropicKnowledgeService`` implementation
- Application uses ``KnowledgeService`` protocol (not the implementation)
- Dependency injection wires up concrete implementations at runtime

**Why this matters:**

- Test domain logic without infrastructure
- Swap AI providers without changing business rules
- Understand system behavior by reading protocols

Domain Layer
------------

**Responsibility:** Core business abstractions with zero infrastructure dependencies.

The domain layer contains:

Models
~~~~~~

Pydantic entities representing business concepts:

- ``Document`` - Content to be processed
- ``Assembly`` - Assembled results
- ``AssemblySpecification`` - Instructions for assembly
- ``Policy`` - Validation and compliance rules
- ``KnowledgeServiceConfig`` - AI service configuration

**What belongs here:**

- Business validation rules
- Domain logic and calculations
- Value objects and enums

**What doesn't belong here:**

- Database code
- API calls
- File I/O
- Framework-specific code

Repository Protocols
~~~~~~~~~~~~~~~~~~~~

Abstract interfaces for persistence:

- Define CRUD operations for domain entities
- Make storage technology pluggable
- No implementation details

Example::

    class DocumentRepository(Protocol):
        async def create(self, doc: Document) -> Document: ...
        async def get(self, id: str) -> Document | None: ...
        async def list(self) -> list[Document]: ...

See :doc:`repositories` for the canonical repository pattern.

Service Protocols
~~~~~~~~~~~~~~~~~

Abstract interfaces for complex operations:

- Define operations delegated to AI and external services
- Make service providers pluggable
- Document expected behavior

Example::

    class KnowledgeService(Protocol):
        async def register_file(self, content: bytes) -> str: ...
        async def query(self, file_id: str, prompt: str) -> dict: ...

See :doc:`services` for the canonical service pattern.

Use Cases
~~~~~~~~~

Business logic orchestration:

- Coordinate repositories and services
- Implement domain workflows
- No knowledge of web frameworks or databases

Examples:

- ``ExtractAssembleData`` - Extract and assemble document data
- ``ValidateDocument`` - Validate document against policies
- ``InitializeSystemData`` - Set up system with seed data

Use cases receive dependencies via dependency injection. See :doc:`protocols` for details.

Application Layer
-----------------

**Responsibility:** Orchestrate use cases and manage application flow.

The application layer contains different types of applications:

**Worker Applications**
    Temporal workers that execute use cases as workflow activities.

    - Workflows are a Temporal-specific decoration of use cases
    - Workers poll Temporal for work
    - Execute use cases in response to workflow steps
    - See :doc:`/architecture/applications/worker` for CEAP workflow details

**API Applications**
    REST endpoints for external access.

    - Execute use cases directly
    - Trigger workflows via Temporal client
    - Handle authentication and authorization
    - Transform requests/responses

**CLI Applications**
    Command-line interfaces for operations.

    - Execute use cases from command line
    - Trigger workflows via Temporal client
    - Administrative and operational tasks

All application types orchestrate use cases from the domain layer. The application type (worker, API, CLI) determines how use cases are invoked, but the use cases themselves remain in the domain layer.

Infrastructure Layer
--------------------

**Responsibility:** Implement domain protocols with concrete technologies.

The infrastructure layer contains:

Repository Implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~

Concrete persistence mechanisms:

- ``MinioDocumentRepository`` - S3-compatible object storage
- ``MemoryDocumentRepository`` - In-memory for testing
- ``PostgreSQLRepository`` - Relational database storage

All implement domain repository protocols. All are interchangeable.

See :doc:`repositories` for implementation details.

Service Implementations
~~~~~~~~~~~~~~~~~~~~~~~

Concrete integrations with AI and external services:

- ``AnthropicKnowledgeService`` - Claude AI integration
- ``OpenAIKnowledgeService`` - GPT integration
- ``LocalLLMService`` - Self-hosted LLM integration
- ``MemoryKnowledgeService`` - Fast mock for testing

All implement domain service protocols. All are pluggable.

See :doc:`services` for implementation details.

Infrastructure Components
~~~~~~~~~~~~~~~~~~~~~~~~~

Supporting components:

- Temporal workers and activities
- MinIO/S3 clients
- Database connections
- HTTP clients for external APIs

These components are used by repository and service implementations.

What Belongs in Each Layer?
----------------------------

Domain Layer Rules
~~~~~~~~~~~~~~~~~~

**Include:**

- Business entities (Pydantic models)
- Business rules and validation
- Protocol definitions
- Use case interfaces
- Value objects, enums

**Exclude:**

- ``import boto3`` ❌
- ``import anthropic`` ❌
- ``import fastapi`` ❌
- ``import temporalio`` ❌
- Database queries ❌
- API calls ❌

Application Layer Rules
~~~~~~~~~~~~~~~~~~~~~~~

**Include:**

- Use case orchestration (calling domain use cases)
- API route handlers (API applications)
- CLI command handlers (CLI applications)
- Temporal workflow definitions (Worker applications)
- Request/response models
- Authentication/authorization
- Application-specific configuration

**Exclude:**

- Business logic (belongs in domain use cases)
- Direct database access (use repositories via DI)
- Direct API calls to services (use service protocols via DI)

**Note:** Workflows are Temporal-specific decorations of use cases, used only in Worker applications. The use case logic itself stays in the domain layer.

Infrastructure Layer Rules
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Include:**

- Repository implementations
- Service implementations
- Database clients
- API clients
- Framework-specific code

**Exclude:**

- Business rules (belongs in domain)
- Workflow orchestration (belongs in application)

Why This Structure?
-------------------

Testability
~~~~~~~~~~~

Test each layer independently:

**Domain Tests**
    Fast unit tests with no infrastructure. Mock repositories and services.

**Application Tests**
    Test workflow logic with Temporal test environment. Use in-memory implementations.

**Infrastructure Tests**
    Integration tests with real databases and services.

Flexibility
~~~~~~~~~~~

Swap implementations without changing business logic:

- Start with in-memory storage, move to PostgreSQL later
- Compare Anthropic vs OpenAI vs local LLMs
- Add new AI providers without touching workflows

Maintainability
~~~~~~~~~~~~~~~

Changes stay localized:

- New business rule? Change domain only.
- New storage backend? Add infrastructure implementation.
- New API endpoint? Add application layer code.

Understanding
~~~~~~~~~~~~~

Architecture reveals intent:

- Protocol definitions show system capabilities
- Use cases show business workflows
- Layer boundaries make dependencies explicit

Example: Layer Interaction
--------------------------

How layers interact in a typical use case execution::

    # Domain Layer - Use Case
    class ExtractAssembleUseCase:
        def __init__(
            self,
            doc_repo: DocumentRepository,      # Protocol
            spec_repo: SpecificationRepository, # Protocol
            knowledge: KnowledgeService         # Protocol
        ):
            self.doc_repo = doc_repo
            self.spec_repo = spec_repo
            self.knowledge = knowledge

        async def execute(self, doc_id: str, spec_id: str):
            # Use protocols, no knowledge of implementations
            doc = await self.doc_repo.get(doc_id)
            spec = await self.spec_repo.get(spec_id)

            # Call AI service via protocol
            extracted = await self.knowledge.query(
                doc.file_id,
                spec.extraction_prompt
            )

            # Business logic
            assembly = self.assemble(extracted, spec)

            return assembly

    # Infrastructure Layer - Service Implementation
    class AnthropicKnowledgeService:
        """Concrete implementation of KnowledgeService protocol"""

        async def query(self, file_id: str, prompt: str) -> dict:
            # Call Anthropic API
            response = await self.client.messages.create(...)
            return response.content

    # Infrastructure Layer - DI Configuration
    def get_knowledge_service() -> KnowledgeService:
        """DI Container configures which implementation to use"""
        return AnthropicKnowledgeService(api_key=settings.api_key)

    # Application Layer - API Application
    @router.post("/extract")
    async def extract_endpoint(
        doc_id: str,
        spec_id: str,
        use_case: ExtractAssembleUseCase = Depends(get_extract_use_case)
    ):
        """API application calls use case"""
        return await use_case.execute(doc_id, spec_id)

    # Application Layer - Worker Application (with Temporal workflow)
    @workflow.defn
    class ExtractAssembleWorkflow:
        """Worker application wraps use case in Temporal workflow"""

        @workflow.run
        async def run(self, doc_id: str, spec_id: str):
            # Workflow is a Temporal-specific decoration
            # Still calls the same domain use case
            result = await workflow.execute_activity(
                extract_assemble_activity,
                args=[doc_id, spec_id]
            )
            return result

Note the flow:

1. **Domain** (use case) defines business logic using protocols
2. **Infrastructure** (service) implements protocols with concrete technology
3. **DI Container** (infrastructure) wires implementations to protocols
4. **Application** (API, Worker, CLI) calls use cases via DI

The use case is in the domain layer. Applications (API, Worker, CLI) invoke it differently, but it's the same use case.

For dependency injection patterns, see :doc:`protocols`.

Common Mistakes
---------------

Mistake 1: Business Logic in Infrastructure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Wrong:**

::

    class AnthropicKnowledgeService:
        async def query(self, file_id: str, prompt: str) -> dict:
            response = await self.client.messages.create(...)

            # Business rule in infrastructure! ❌
            if response.validation_score < 0.8:
                raise ValidationError("Score too low")

            return response.content

**Right:**

::

    # Infrastructure just calls API
    class AnthropicKnowledgeService:
        async def query(self, file_id: str, prompt: str) -> dict:
            response = await self.client.messages.create(...)
            return response.content

    # Domain implements business rule ✓
    class ValidateResultUseCase:
        async def execute(self, result: dict):
            if result["validation_score"] < 0.8:
                raise ValidationError("Score too low")

Mistake 2: Infrastructure Imports in Domain
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Wrong:**

::

    # In domain layer ❌
    from anthropic import Anthropic

    class ExtractDataUseCase:
        def __init__(self, api_key: str):
            self.client = Anthropic(api_key=api_key)

**Right:**

::

    # In domain layer ✓
    class ExtractDataUseCase:
        def __init__(self, knowledge: KnowledgeService):
            self.knowledge = knowledge

    # In infrastructure layer ✓
    from anthropic import Anthropic

    class AnthropicKnowledgeService:
        def __init__(self, api_key: str):
            self.client = Anthropic(api_key=api_key)

Mistake 3: Use Cases in Infrastructure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Wrong:**

::

    class DocumentRepository:
        async def create_and_validate(self, doc: Document):
            # Repository doing too much! ❌
            await self.validate(doc)
            await self.store(doc)
            await self.notify_watchers(doc)

**Right:**

::

    # Repository only stores ✓
    class DocumentRepository:
        async def create(self, doc: Document):
            await self.store(doc)

    # Use case orchestrates ✓
    class CreateDocumentUseCase:
        async def execute(self, doc: Document):
            await self.validator.validate(doc)
            await self.repo.create(doc)
            await self.notifier.notify(doc)

Summary
-------

Three layers with one rule:

**Domain** - Business logic, zero dependencies
    Models, protocols, use cases

**Application** - Orchestration (CLI, API, Workers)
    Use case invocation, workflows (Worker-specific), API endpoints, CLI commands

**Infrastructure** - Concrete implementations
    Repositories, services, clients, DI container

**The Dependency Rule** - Dependencies point inward
    Application depends on DI Container, DI Container configures Infrastructure, Infrastructure implements Domain protocols

This structure makes AI systems:

- Testable (mock any component)
- Flexible (swap implementations via DI)
- Maintainable (changes stay localized)
- Understandable (architecture reveals intent)

For protocol-based design and DI, see :doc:`protocols`.

For persistence patterns, see :doc:`repositories`.

For AI service patterns, see :doc:`services`.

For applications (Worker, API, CLI), see :doc:`/architecture/applications/index`.
