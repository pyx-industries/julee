Clean Architecture
==================

Both the :doc:`Julee Framework </architecture/framework>` and :doc:`Julee Solutions </architecture/solutions/index>`
organize their code using Robert C Martin's "Clean Architecture" principles.
This document will just focus on Julee's interpretation and implementation.

Clean Architcture is strict about how the dependencies in code are organised.
There are other similar schemes, such as Alistair Cockbourn's "Hexagonal Architecture"
(a.k.a "ports and adapters"), which share the same core goals
of **dependency inversion** and **separation of concerns**. They both:

* Place business logic at the center, isolated from external concerns
* Make external dependencies (databases, UI, external services) plug into the core rather than vice versa
* Use dependency inversion to point dependencies inward
* Aim for testability and flexibility in swapping implementations

For comparison, Hexagonal architecture uses a simpler two-part model
(inside/outside) focused on ports and adapters,
without prescribing how to structure the business logic inside.
Clean Architecture defines multiple concentric layers
with specific responsibilities for each.
Essentially, Clean Architecture is more prescriptive
about the internal organization while Hexagonal Architecture
is more minimal and focused on the boundary between core and infrastructure.
It is essentially a 3 layer, rather than a 2 layer system.

.. uml:: ../diagrams/clean_architecture_layers.puml


Demonstration
-------------

One of the :doc:`batteries included </architecture/solutions/batteries-included>` features
is a "Capture, Extract, Assembly, Publish" workflow (CEAP).
This is a general purpose AI heuristic
which is useful in a lot of circumstances.
Rather than talking about the clean architecture in theory,
we will walk through a part of this by way of an example.

This is an automated process with no user interaction,
so it is done by an application called a Worker.
We will specifically look at the :doc:`pipeline </architecture/solutions/pipelines>`
called :py:class:`~julee.domain.use_cases.ExtractAssembleDataUseCase`.
This is the most complicated and interesting part of CEAP.

.. uml:: ../diagrams/ceap_workflow_sequence.puml

A usecase is usually specific to a business domain,
CEAP is unusual because it's a generic, reusable pattern.
That's why it's part of the framework,
so you can reuse it without having to reinvent the wheel.

This usecase is understandable and testable,
but it leaves a lot to the imagination.
What is :py:class:`~julee.services.KnowledgeService`,
:py:class:`~julee.domain.repositories.DocumentRepository`,
:py:class:`~julee.domain.repositories.AssemblyRepository`,
:py:class:`~julee.domain.repositories.AssemblySpecificationRepository`,
:py:class:`~julee.domain.repositories.KnowledgeServiceQueryRepository`, and
:py:class:`~julee.domain.repositories.KnowledgeServiceConfigRepository`?
How do they work? Those questions are answered separately.

The repositories are "things that store and access data".
As long as the usecase can use them,
it shouldn't have to care about how they work.
So "what is the repository" is first defined in the abstract,
using a python Protocol specification,
which is part of the domain model.
These definitions are:

- :py:class:`~julee.domain.repositories.DocumentRepository`
- :py:class:`~julee.domain.repositories.AssemblyRepository`
- :py:class:`~julee.domain.repositories.AssemblySpecificationRepository`
- :py:class:`~julee.domain.repositories.KnowledgeServiceQueryRepository`
- :py:class:`~julee.domain.repositories.KnowledgeServiceConfigRepository`

Second, "how do they work" is an infrastructure concern.
There is code that implements the protocol using technology:

**MinIO implementations** (production, S3-compatible object storage):

- :py:class:`~julee.repositories.minio.MinioDocumentRepository`
- :py:class:`~julee.repositories.minio.MinioAssemblyRepository`
- :py:class:`~julee.repositories.minio.MinioAssemblySpecificationRepository`
- :py:class:`~julee.repositories.minio.MinioKnowledgeServiceQueryRepository`
- :py:class:`~julee.repositories.minio.MinioKnowledgeServiceConfigRepository`

**Memory implementations** (testing):

- :py:class:`~julee.repositories.memory.MemoryDocumentRepository`
- :py:class:`~julee.repositories.memory.MemoryAssemblyRepository`
- :py:class:`~julee.repositories.memory.MemoryAssemblySpecificationRepository`
- :py:class:`~julee.repositories.memory.MemoryKnowledgeServiceQueryRepository`
- :py:class:`~julee.repositories.memory.MemoryKnowledgeServiceConfigRepository`

Those do the dirty work of writing to disk,
talking to databases, making API calls,
or whatever else it is that they need to do
to store and access data.

Note how the protocols are strongly typed.
They proscribe that inputs and outputs are either
domain model classes or simple primitives.
The repositories give and take:

- :py:class:`~julee.domain.models.Document`
- :py:class:`~julee.domain.models.Assembly`
- :py:class:`~julee.domain.models.AssemblySpecification`
- :py:class:`~julee.domain.models.KnowledgeServiceQuery`
- :py:class:`~julee.domain.models.KnowledgeServiceConfig`

These domain model abstractions serve to protect the usecase
from the vaguries of the external systems.
This also makes the implementations "swappable",
anything that conforms to the protocol will do.
This is how it is possible for the Dependency Injection
(DI) container to do it's job, it simply provides the application
with "one of each of the repositories that it needs",
and henceforth the usecases just use them.


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

Use cases receive dependencies via :doc:`dependency injection <protocols>`.

Application Layer
-----------------

**Responsibility:** Orchestrate use cases and manage application flow.

The application layer contains different types of applications:

**Worker Applications**
    Temporal workers that execute use cases as workflow activities.

    - Workflows are a Temporal-specific decoration of use cases
    - Workers poll Temporal for work
    - Execute use cases in response to workflow steps
    - :doc:`CEAP workflows </architecture/applications/worker>` implement the pattern

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
