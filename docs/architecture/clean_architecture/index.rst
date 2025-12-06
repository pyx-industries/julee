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


Framework Layers vs Solution Layers
-----------------------------------

Before diving into the layers, remember the key distinction:
**a framework and a solution are different beasts.**

Julee is a framework—its "domain" is the vocabulary for building digital supply chains.
When you look at Julee's ``domain/`` directory, you see framework concepts:
``Repository``, ``Service``, ``UseCase``, ``Entity``.

Your solution uses this vocabulary to express *your* business domain.
Your ``domain/`` directories (within your bounded contexts) contain
*your* business entities: ``Invoice``, ``Patient``, ``Order``.

::

    # Julee's domain layer (framework vocabulary)
    julee/domain/
      repositories/       # Repository protocol definitions
      models/             # Base model patterns
      use_cases/          # Use case patterns

    # Your solution's domain layer (your business)
    my_app/billing/domain/
      invoice.py          # Your Invoice entity
      payment.py          # Your Payment entity
      invoice_repository.py  # Protocol for your entity

The Clean Architecture principles apply at both levels,
but what goes *in* each layer differs between framework and solution.


The Dependency Rule
-------------------

**Dependencies point inward toward the domain.**

The core principle: Outer layers depend on inner layers. Inner layers never depend on outer layers.

.. uml:: ../diagrams/clean_architecture_layers.puml

This means:

- Domain defines :py:class:`~julee.services.knowledge_service.KnowledgeService` protocol
- Infrastructure provides :py:class:`~julee.services.knowledge_service.anthropic.AnthropicKnowledgeService` implementation
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

Pydantic entities representing business concepts.

**In the Julee framework**, the domain models are generic building blocks
that many solutions might use:

- :py:class:`~julee.domain.models.Document` - Content to be processed
- :py:class:`~julee.domain.models.Assembly` - Assembled results
- :py:class:`~julee.domain.models.AssemblySpecification` - Instructions for assembly
- :py:class:`~julee.domain.models.Policy` - Validation and compliance rules
- :py:class:`~julee.domain.models.KnowledgeServiceConfig` - AI service configuration

**In your solution**, the domain models are *your* business entities::

    # my_app/billing/domain/invoice.py
    from pydantic import BaseModel
    from decimal import Decimal

    class Invoice(BaseModel):
        """An invoice in the billing context."""
        id: str
        customer_id: str
        line_items: list[LineItem]
        total: Decimal
        status: InvoiceStatus

You may extend or compose Julee's models, or define entirely your own.

**What belongs in domain models:**

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

**Julee provides** repository protocols for its framework entities::

    class DocumentRepository(Protocol):
        async def create(self, doc: Document) -> Document: ...
        async def get(self, id: str) -> Document | None: ...
        async def list(self) -> list[Document]: ...

**Your solution defines** repository protocols for your entities::

    # my_app/billing/domain/invoice_repository.py
    class InvoiceRepository(Protocol):
        async def create(self, invoice: Invoice) -> Invoice: ...
        async def get(self, id: str) -> Invoice | None: ...
        async def list_by_customer(self, customer_id: str) -> list[Invoice]: ...

Service Protocols
~~~~~~~~~~~~~~~~~

Abstract interfaces for complex operations:

- Define operations delegated to AI and external services
- Make service providers pluggable
- Document expected behavior

**Julee provides** service protocols for common AI operations::

    class KnowledgeService(Protocol):
        async def register_file(self, content: bytes) -> str: ...
        async def query(self, file_id: str, prompt: str) -> dict: ...

**Your solution defines** service protocols for your specific needs::

    # my_app/billing/domain/tax_service.py
    class TaxService(Protocol):
        async def calculate_tax(self, invoice: Invoice) -> TaxResult: ...

Use Cases
~~~~~~~~~

Business logic orchestration:

- Coordinate repositories and services
- Implement domain workflows
- No knowledge of web frameworks or databases

**Julee provides** use cases for common document processing patterns:

- :py:class:`~julee.domain.use_cases.ExtractAssembleDataUseCase` - Extract and assemble document data
- :py:class:`~julee.domain.use_cases.ValidateDocumentUseCase` - Validate document against policies
- :py:class:`~julee.domain.use_cases.InitializeSystemDataUseCase` - Set up system with seed data

**Your solution defines** use cases for your business operations::

    # my_app/billing/use_cases/process_invoice.py
    class ProcessInvoiceUseCase:
        def __init__(
            self,
            invoice_repo: InvoiceRepository,
            tax_service: TaxService,
            knowledge_service: KnowledgeService  # from Julee
        ):
            self.invoice_repo = invoice_repo
            self.tax_service = tax_service
            self.knowledge_service = knowledge_service

        async def execute(self, invoice_id: str) -> Invoice:
            invoice = await self.invoice_repo.get(invoice_id)
            tax = await self.tax_service.calculate_tax(invoice)
            # ... business logic
            return await self.invoice_repo.update(invoice)

Use cases receive dependencies via dependency injection (see :doc:`protocols`).

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

- :py:class:`~julee.repositories.minio.MinioDocumentRepository` - S3-compatible object storage
- :py:class:`~julee.repositories.memory.MemoryDocumentRepository` - In-memory for testing
- ``PostgreSQLRepository`` - Relational database storage

All implement domain :doc:`repository <repositories>` protocols.

Service Implementations
~~~~~~~~~~~~~~~~~~~~~~~

Concrete integrations with AI and external services:

- :py:class:`~julee.services.knowledge_service.anthropic.AnthropicKnowledgeService` - Claude AI integration
- ``OpenAIKnowledgeService`` - GPT integration
- ``LocalLLMService`` - Self-hosted LLM integration
- :py:class:`~julee.services.knowledge_service.memory.MemoryKnowledgeService` - Fast mock for testing

All implement domain :doc:`service <services>` protocols.

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

Three layers, one rule: **dependencies point inward toward the domain**. Domain defines protocols, infrastructure implements them, applications orchestrate via DI.
