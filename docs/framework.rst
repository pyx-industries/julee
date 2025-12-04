Framework Concepts
==================

What is Julee?
--------------

**Julee is a batteries-included framework** for building document processing applications using the **Capture, Extract, Assemble, Publish (CEAP)** pattern with Temporal workflows.

Like Django provides an admin interface and ORM out-of-the-box, Julee provides:

- **CEAP Workflows**: Production-ready workflows for document processing
- **Repository Layer**: Storage abstractions with implementations
- **Service Layer**: Integration patterns for external services
- **Domain Models**: Ready-to-use or extend domain entities
- **Dependency Injection**: Configuration and service wiring

Framework vs Application vs Services
-------------------------------------

Understanding the boundaries:

**Julee Framework**
    The installable Python package providing CEAP workflows, domain models, repository implementations, service protocols, and infrastructure integrations.

**Julee Application**
    Your specific application built with Julee. Defines domain models, configures services, and uses Julee's workflows.

**Services**
    Supply chain actors your application depends on. Can be:

    - **Bundled with your app**: Custom logic deployed with your app
    - **Third-party APIs**: External supply chain partners (Anthropic, SendGrid, etc.)
    - **Self-hosted**: Services you deploy and operate (local LLM, etc.)

Repositories vs Services
------------------------

Understanding the distinction:

**Repositories**
    Persistence mechanisms that implement simple CRUD operations:

    - **Store and retrieve** domain entities
    - Abstract the storage technology (MinIO, PostgreSQL, memory, etc.)
    - Multiple implementations are **pluggable** via repository protocols
    - Examples: ``DocumentRepository``, ``AssemblyRepository``
    - Operations: create, get, list, update, delete

**Services**
    Complex operations delegated to supply chain actors:

    - Perform domain logic **beyond simple persistence**
    - Often **delegated to third-party providers**
    - Act as **supply chain actors** in the digital product supply chain
    - Examples: ``KnowledgeService`` (AI extraction), ``ValidationService``, ``NotificationService``
    - Operations: extract knowledge, validate content, generate insights, send notifications

**Key difference**: Repositories store things, Services do things.

Clean Architecture Layers
--------------------------

Julee implements Clean Architecture with proper dependency inversion:

.. uml::

   @startuml
   !include <C4/C4_Component>

   rectangle "Clean Architecture" {
       together {
           component "Presentation\n(API/UI)" as pres #LightBlue
           component "Infrastructure\n(Repos, Services)" as infra #LightGreen
       }
       component "Application\n(Use Cases)" as app #LightYellow
       component "Domain\n(Models, Protocols)" as domain #Orange
   }

   pres -down-> app : uses
   app -down-> domain : uses
   infra -up-> domain : implements protocols
   pres .down.> infra : depends on (via DI)
   app .down.> infra : depends on (via DI)

   note right of domain
     Core domain has NO dependencies
     on outer layers. Defines protocols
     that infrastructure implements.
   end note
   @enduml

**Dependency Rule**: Dependencies point inward toward the domain. Infrastructure implements domain protocols.

Domain Layer
~~~~~~~~~~~~

The domain layer defines core business abstractions with **no infrastructure dependencies**:

**Models**
    - Pydantic domain entities: Document, Assembly, AssemblySpecification, Policy
    - Validation rules and business logic
    - Value objects and enums

**Repository Protocols**
    - Abstract interfaces for **persistence**
    - Define CRUD operations for domain entities
    - Make storage pluggable (MinIO, PostgreSQL, memory)

**Service Protocols**
    - Abstract interfaces for **complex operations**
    - Define operations delegated to supply chain actors
    - Make service providers pluggable (Anthropic, OpenAI, local)

**Use Cases**
    - Business logic orchestration
    - Coordinate repositories (for persistence) and services (for operations)
    - Examples: ``ExtractAssembleData``, ``ValidateDocument``

Application Layer
~~~~~~~~~~~~~~~~~

Orchestrates use cases:

**Workflows**
    - Temporal workflow definitions
    - Call use cases, manage long-running processes
    - Error handling and retries

**API** (optional)
    - REST endpoints
    - Triggers workflows
    - Direct use case calls

Infrastructure Layer
~~~~~~~~~~~~~~~~~~~~

Implements domain protocols:

**Repository Implementations**
    - Pluggable persistence mechanisms
    - MinIO/S3, memory, PostgreSQL implementations
    - Swap without changing domain logic

**Service Implementations**
    - Supply chain actors providing complex operations
    - Third-party APIs, self-hosted, or bundled
    - Handle operations beyond simple persistence

CEAP Workflows (Batteries Included)
------------------------------------

Like Django Admin, Julee provides production-ready workflows:

**ExtractAssembleWorkflow**
    Core CEAP workflow for document processing:

    1. Retrieves document from storage
    2. Fetches assembly specification
    3. Executes knowledge service queries for extraction
    4. Assembles results according to specification
    5. Stores final assembly

**ValidateDocumentWorkflow**
    Document validation against policies:

    1. Retrieves document
    2. Fetches validation policies
    3. Executes validation rules
    4. Records validation results

**Workflow Customization**:

- Use workflows as-is with configuration
- Extend workflows for custom behavior
- Build new workflows using Julee patterns

Service Architecture (Supply Chain)
------------------------------------

Services are **supply chain actors** performing complex operations:

.. uml::

   @startuml
   !include <C4/C4_Component>

   Component(app, "Julee Application\n(Supply Chain Orchestrator)")

   together {
       Component(bundled, "Bundled Service", "Part of deployment")
       System_Ext(thirdparty, "Third-party Service", "Supply chain actor")
       Component(local, "Self-hosted Service", "Local supply chain actor")
   }

   app -right-> bundled : direct
   app -down-> thirdparty : HTTP/API
   app -left-> local : network/local

   note bottom of app
     Services accessed via protocol interfaces.
     Service providers are pluggable via DI.
   end note

   note right of thirdparty
     Supply chain actors:
     - AI/LLM providers (Anthropic, OpenAI)
     - Validation services
     - Notification services
     - Analytics services
   end note
   @enduml

**Service Types**:

1. **Bundled**: Custom business logic you own, deployed with your app
2. **Third-party APIs**: External supply chain partners (Anthropic, SendGrid, Stripe)
3. **Self-hosted**: Services you deploy and operate (local LLM, custom processors)

**Not Services** (Infrastructure):

- MinIO/S3: Storage (repository implementation)
- Temporal: Workflow orchestration (infrastructure)
- PostgreSQL: Database (repository implementation)

Dependency Injection
--------------------

Julee uses FastAPI's dependency injection system:

.. uml::

   @startuml
   !include <C4/C4_Component>

   Component(di, "DI Container", "FastAPI Depends")
   Component(config, "Configuration", "Environment vars, settings")
   Component(repos, "Repository Factories", "Create repo instances")
   Component(services, "Service Factories", "Create service instances")
   Component(usecases, "Use Case Factories", "Wire dependencies")

   config -down-> di : provides
   di -down-> repos : creates
   di -down-> services : creates
   di -down-> usecases : injects deps
   @enduml

**Configuration Flow**:

1. Application loads configuration (env vars, settings)
2. DI container registers factory functions
3. Factories create repository and service instances
4. Use cases receive dependencies via injection
5. Workflows and API use configured dependencies

Example::

    # Repository factory
    async def get_document_repository() -> DocumentRepository:
        return MinioDocumentRepository(get_minio_client())

    # Service factory
    async def get_knowledge_service() -> KnowledgeService:
        config = get_config()
        return AnthropicKnowledgeService(api_key=config.api_key)

    # Use case with injected dependencies
    async def extract_data(
        doc_id: str,
        doc_repo: DocumentRepository = Depends(get_document_repository),
        knowledge: KnowledgeService = Depends(get_knowledge_service)
    ):
        doc = await doc_repo.get(doc_id)
        result = await knowledge.query(doc.content, "Extract key points")
        return result

Repository Pattern
------------------

Repositories implement protocols defined in domain::

    # Domain defines protocol (no implementation)
    class DocumentRepository(Protocol):
        async def create(self, doc: Document) -> Document: ...
        async def get(self, id: str) -> Document | None: ...
        async def list(self) -> list[Document]: ...

    # Infrastructure implements
    class MinioDocumentRepository:
        async def create(self, doc: Document) -> Document:
            # Store in MinIO
            await self.client.put_object(...)
            return doc

    # DI provides implementation
    def get_document_repository() -> DocumentRepository:
        return MinioDocumentRepository(get_minio_client())

**Benefits**:

- Testability: Mock repositories for testing
- Flexibility: Swap storage backends
- Type Safety: Full IDE and mypy support

Service Protocol Pattern
------------------------

Services implement protocols for complex operations::

    # Domain defines the protocol
    class KnowledgeService(Protocol):
        async def register_file(self, content: bytes) -> str: ...
        async def query(self, file_id: str, prompt: str) -> dict: ...

    # Infrastructure provides implementations
    class AnthropicKnowledgeService:
        """Third-party API service"""
        async def register_file(self, content: bytes) -> str:
            # Call Anthropic API
            pass

    class LocalLLMService:
        """Self-hosted service"""
        async def register_file(self, content: bytes) -> str:
            # Call local LLM
            pass

Testing Your Application
------------------------

Julee provides test implementations:

**Unit Tests**::

    from julee.repositories.memory import MemoryDocumentRepository
    from julee.services.knowledge_service.memory import MemoryKnowledgeService

    async def test_use_case():
        # Use in-memory implementations
        doc_repo = MemoryDocumentRepository()
        knowledge = MemoryKnowledgeService()

        result = await extract_assemble_use_case(
            doc_repo=doc_repo,
            knowledge_service=knowledge
        )

**Integration Tests**: Test with real services (MinIO, Temporal)

**Workflow Tests**: Use Temporal test server

Building Your Application
--------------------------

Steps to build a Julee application:

1. **Install Julee**::

       pip install julee

2. **Define Domain Models**::

       from pydantic import BaseModel

       class Invoice(BaseModel):
           number: str
           amount: float

3. **Configure Services** (set up DI)::

       def get_knowledge_service() -> KnowledgeService:
           return AnthropicKnowledgeService(api_key=settings.api_key)

4. **Use CEAP Workflows**::

       worker = Worker(
           client,
           task_queue="my-queue",
           workflows=[ExtractAssembleWorkflow],
           activities=get_all_activities()
       )

5. **Deploy** with required services (Temporal, Storage, etc.)

Extensibility
-------------

Julee is designed to be extended:

- **Custom Domain Models**: Define your entities
- **Custom Repositories**: Implement new storage backends
- **Custom Services**: Add service implementations
- **Custom Use Cases**: Build new business logic
- **Custom Workflows**: Create new Temporal workflows
- **Override Defaults**: Replace any component via DI
