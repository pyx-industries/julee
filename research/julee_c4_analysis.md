# Julee Architecture Through the C4 Lens

This document analyses the Julee platform architecture using C4 model semantics, mapping architectural concepts to Software Systems, Containers, Components, and Code abstractions as defined in [C4 Fundamentals](./c4_fundamentals.md).

---

## 1. Executive Summary

Julee is a Python framework for building resilient, auditable business processes using Temporal workflows. It emphasises accountability, transparency, and compliance audit trails—particularly suited for "digital product passports" and supply chain provenance.

The architecture follows **Clean Architecture** principles with strict separation between domain, application, and infrastructure layers. This maps naturally to C4's hierarchical abstractions.

---

## 2. System Context (Level 1)

### 2.1 The Julee Software System

**Definition:** Julee is a software system that delivers document processing and assembly capabilities to its users. It provides capture, extraction, assembly, and publication (CEAP) workflows with full audit trails.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SYSTEM CONTEXT                                 │
│                                                                         │
│    ┌──────────────┐                           ┌──────────────┐          │
│    │   Platform   │                           │Administrator │          │
│    │     User     │                           │              │          │
│    └──────┬───────┘                           └──────┬───────┘          │
│           │ Uploads documents                        │ Configures       │
│           │ Views assemblies                         │ pipelines        │
│           ▼                                          ▼                  │
│    ┌─────────────────────────────────────────────────────────┐          │
│    │                    JULEE PLATFORM                       │          │
│    │         Document Processing & Assembly System           │          │
│    └─────────────────────────────────────────────────────────┘          │
│           │                    │                    │                   │
│           ▼                    ▼                    ▼                   │
│    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐          │
│    │   Temporal   │     │  Anthropic   │     │    MinIO     │          │
│    │   [External] │     │    [Ext]     │     │   [External] │          │
│    └──────────────┘     └──────────────┘     └──────────────┘          │
│    Workflow             AI Knowledge         Object Storage            │
│    Orchestration        Service                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Persons (Actors)

| Person | Description |
|--------|-------------|
| **Platform User** | Submits documents for processing, views assembled outputs |
| **Administrator** | Configures processing pipelines, assembly specifications, and policies |
| **Developer** | Extends the platform with new accelerators and integrations |

### 2.3 External Software Systems

| System | Role | Relationship |
|--------|------|--------------|
| **Temporal** | Workflow orchestration server | Julee submits workflows and polls for tasks |
| **Anthropic API** | AI/ML knowledge service for document understanding | Julee queries for content extraction |
| **MinIO** | S3-compatible object storage | Julee persists documents and configurations |
| **PostgreSQL** | Temporal's persistence backend | Indirect dependency via Temporal |

---

## 3. Container Diagram (Level 2)

The Julee software system decomposes into the following containers:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         JULEE PLATFORM                                   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      API Container                               │    │
│  │                   [FastAPI + Uvicorn]                           │    │
│  │         REST endpoints for document & workflow management        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│           │                                          │                  │
│           │ Starts workflows                         │ Reads/Writes     │
│           ▼                                          ▼                  │
│  ┌─────────────────────┐                    ┌─────────────────────┐    │
│  │   Worker Container  │                    │  Object Store       │    │
│  │   [Temporal Worker] │───Reads/Writes────►│  [MinIO]            │    │
│  │   Executes workflow │                    │  Document storage   │    │
│  │   activities        │                    └─────────────────────┘    │
│  └─────────────────────┘                                               │
│           │                                                             │
│           │ Polls tasks                                                │
│           ▼                                                             │
│  ┌─────────────────────┐         ┌─────────────────────────────────┐   │
│  │   Temporal Server   │         │   Documentation System          │   │
│  │   [External]        │         │   [HCD MCP + API + Sphinx]      │   │
│  └─────────────────────┘         │   Domain model for HCD semantics │   │
│                                  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Container Definitions

| Container | Technology | Responsibility |
|-----------|------------|----------------|
| **API** | FastAPI, Uvicorn | HTTP REST endpoints for CEAP workflow management. Entry point: `src/julee/api/app.py` |
| **Worker** | Temporal Client, Python async | Executes Temporal workflows and activities. Entry point: `src/julee/worker.py` |
| **Object Store** | MinIO (S3-compatible) | Persists documents, configurations, and assemblies |
| **Documentation System** | Sphinx, MCP, FastAPI | HCD domain model with MCP server and REST API. Entry points: `src/julee/docs/hcd_mcp/server.py`, `src/julee/docs/hcd_api/app.py` |

### 3.2 Container Relationships

| From | To | Description | Technology |
|------|-----|-------------|------------|
| API | Temporal | Starts workflows | Temporal Client |
| API | MinIO | Reads/writes documents | S3 API |
| Worker | Temporal | Polls for tasks | Temporal Client |
| Worker | MinIO | Reads/writes documents | S3 API |
| Worker | Anthropic | Queries knowledge service | HTTPS |

---

## 4. Component Diagram (Level 3)

### 4.1 API Container Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         API CONTAINER                                    │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                         Routers                                   │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │   │
│  │  │  documents   │ │  workflows   │ │   system     │              │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘              │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │   │
│  │  │ assembly_    │ │ knowledge_   │ │ knowledge_   │              │   │
│  │  │ specs        │ │ configs      │ │ queries      │              │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│           │                                                             │
│           │ Injects dependencies                                       │
│           ▼                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Dependencies                                   │   │
│  │         [DependencyContainer with singleton lifecycle]            │   │
│  │         Temporal client, MinIO client, Repositories               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│           │                                                             │
│           │ Invokes                                                    │
│           ▼                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     Use Cases                                     │   │
│  │    ExtractAssembleDataUseCase, ValidateDocumentUseCase           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│           │                                                             │
│           │ Uses                                                       │
│           ▼                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Repositories                                   │   │
│  │    DocumentRepository, AssemblyRepository,                        │   │
│  │    AssemblySpecificationRepository, PolicyRepository              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

#### API Container Component Definitions

| Component | Technology | Responsibility | Location |
|-----------|------------|----------------|----------|
| **Routers** | FastAPI | HTTP endpoint handlers | `src/julee/api/routers/` |
| **Dependencies** | Python | Dependency injection container | `src/julee/api/dependencies.py` |
| **Use Cases** | Python | Business logic orchestration | `src/julee/domain/use_cases/` |
| **Repositories** | Python protocols | Data access abstraction | `src/julee/domain/repositories/` |

### 4.2 Worker Container Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        WORKER CONTAINER                                  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                        Workflows                                  │   │
│  │    ExtractAssembleWorkflow, ValidateDocumentWorkflow             │   │
│  │    [Temporal @workflow.defn decorated classes]                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│           │                                                             │
│           │ Delegates to                                               │
│           ▼                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                        Activities                                 │   │
│  │    Repository operations, Knowledge service calls                 │   │
│  │    [Temporal @activity.defn decorated functions]                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│           │                                                             │
│           │ Uses                                                       │
│           ▼                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                   Repository Proxies                              │   │
│  │    WorkflowDocumentRepositoryProxy, etc.                         │   │
│  │    [Delegate repository calls to activities for determinism]     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│           │                                                             │
│           │ Invokes                                                    │
│           ▼                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     Use Cases                                     │   │
│  │    ExtractAssembleDataUseCase (same as API, different repos)     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Worker Container Component Definitions

| Component | Technology | Responsibility | Location |
|-----------|------------|----------------|----------|
| **Workflows** | Temporal SDK | Orchestrate multi-step processes | `src/julee/workflows/` |
| **Activities** | Temporal SDK | Execute I/O operations | `src/julee/workflows/activities/` |
| **Repository Proxies** | Python | Delegate to activities for determinism | `src/julee/repositories/temporal/` |
| **Use Cases** | Python | Business logic (shared with API) | `src/julee/domain/use_cases/` |

### 4.3 Domain Layer Components

The domain layer is shared across containers and represents the core business logic:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                                     │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                         Models                                    │   │
│  │  Document, Assembly, AssemblySpecification, Policy,              │   │
│  │  DocumentPolicyValidation, KnowledgeServiceConfig,               │   │
│  │  KnowledgeServiceQuery                                           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Repository Protocols                           │   │
│  │  BaseRepository[T] (generic CRUD)                                │   │
│  │  ├── DocumentRepository                                          │   │
│  │  ├── AssemblyRepository                                          │   │
│  │  ├── AssemblySpecificationRepository                             │   │
│  │  ├── PolicyRepository                                            │   │
│  │  ├── DocumentPolicyValidationRepository                          │   │
│  │  ├── KnowledgeServiceConfigRepository                            │   │
│  │  └── KnowledgeServiceQueryRepository                             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                       Use Cases                                   │   │
│  │  ExtractAssembleDataUseCase - Main CEAP business logic           │   │
│  │  ValidateDocumentUseCase - Policy validation                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Documentation System Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DOCUMENTATION SYSTEM                                  │
│                                                                         │
│  ┌──────────────────────┐  ┌──────────────────────┐                    │
│  │   HCD MCP Server     │  │   HCD REST API       │                    │
│  │   [MCP Protocol]     │  │   [FastAPI]          │                    │
│  │   Claude integration │  │   HTTP endpoints     │                    │
│  └──────────────────────┘  └──────────────────────┘                    │
│           │                         │                                   │
│           └────────────┬────────────┘                                   │
│                        │                                                │
│                        ▼                                                │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Sphinx HCD Extension                           │   │
│  │    Domain models: Story, Epic, Journey, Persona, App,            │   │
│  │    Accelerator, Integration                                       │   │
│  │    Repositories, Use Cases, Sphinx Directives                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Code Level (Level 4)

### 5.1 Key Domain Models

```python
# src/julee/domain/models/document.py
@dataclass
class Document:
    id: str
    name: str
    content_stream: ContentStream
    status: DocumentStatus  # CAPTURED → REGISTERED → ... → PUBLISHED/FAILED
    metadata: dict
    multihash: str          # Content integrity
    created_at: datetime
    updated_at: datetime
```

```python
# src/julee/domain/models/assembly.py
@dataclass
class Assembly:
    id: str
    document_id: str
    assembly_specification_id: str
    assembled_document_id: str | None
    status: AssemblyStatus  # INITIALIZED → COMPLETE/FAILED
    created_at: datetime
```

### 5.2 Repository Protocol Pattern

```python
# src/julee/domain/repositories/base.py
@runtime_checkable
class BaseRepository(Protocol[T]):
    async def get(self, entity_id: str) -> T | None: ...
    async def save(self, entity: T) -> None: ...
    async def list_all(self) -> list[T]: ...
    async def generate_id(self) -> str: ...
```

### 5.3 Repository Implementations

| Implementation | Technology | Purpose | Location |
|----------------|------------|---------|----------|
| **Memory** | Python dict | Testing, development | `src/julee/repositories/memory/` |
| **MinIO** | boto3/S3 | Production persistence | `src/julee/repositories/minio/` |
| **Temporal** | Temporal activities | Workflow context proxies | `src/julee/repositories/temporal/` |

### 5.4 Knowledge Service Abstraction

```python
# src/julee/services/knowledge_service/knowledge_service.py
class KnowledgeService(Protocol):
    async def register_file(self, document: Document) -> FileRegistrationResult: ...
    async def execute_query(self, config: KnowledgeServiceConfig, query: str) -> QueryResult: ...
```

| Implementation | Purpose | Location |
|----------------|---------|----------|
| **AnthropicKnowledgeService** | Production AI integration | `src/julee/services/knowledge_service/anthropic.py` |
| **MemoryKnowledgeService** | Testing | `src/julee/services/knowledge_service/memory.py` |

### 5.5 Temporal Workflow Pattern

```python
# src/julee/workflows/extract_assemble.py
@workflow.defn
class ExtractAssembleWorkflow:
    @workflow.run
    async def run(self, document_id: str, spec_id: str) -> Assembly:
        # Create proxy repositories (delegate to activities)
        doc_repo = WorkflowDocumentRepositoryProxy()

        # Create use case with injected dependencies
        use_case = ExtractAssembleDataUseCase(
            document_repo=doc_repo,
            assembly_repo=assembly_repo,
            knowledge_service=knowledge_service
        )

        # Execute business logic
        return await use_case.assemble_data(document_id, spec_id)
```

---

## 6. Architectural Patterns Mapped to C4

### 6.1 Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│  C4 Component Level: Presentation                                        │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Routers, MCP Server, CLI                                 │  │
│  └───────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│  C4 Component Level: Application                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Use Cases: ExtractAssembleDataUseCase, ValidateDocumentUseCase   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│  C4 Component Level: Domain                                              │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Models: Document, Assembly, Policy                               │  │
│  │  Repository Protocols, Service Protocols                          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│  C4 Component Level: Infrastructure                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  MinIO Repositories, Temporal Activities, Anthropic Service       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Accelerators as Contrib Modules

Julee uses "Accelerators" as self-contained, composable solutions. In C4 terms, each accelerator is a **component group** that can be deployed independently or composed into larger systems.

**Example: Polling Accelerator** (`src/julee/contrib/polling/`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    POLLING ACCELERATOR                                   │
│                                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │    Domain      │  │  Use Cases     │  │ Infrastructure │            │
│  │  PollingConfig │  │  PollEndpoint  │  │  HTTPPoller    │            │
│  │  PollingResult │  │  DetectChange  │  │  TemporalMgr   │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Dependency Injection Pattern

The architecture uses constructor-based injection with protocol types, enabling:
- **Testing:** Swap MinIO repos for Memory repos
- **Workflow context:** Swap direct repos for Temporal proxy repos
- **Flexibility:** Multiple implementations per protocol

---

## 7. Data Flow: CEAP Workflow

### 7.1 Dynamic View

```
┌────────────────────────────────────────────────────────────────────────┐
│                    CEAP WORKFLOW SEQUENCE                               │
│                                                                        │
│  User ──1. Upload──► API ──2. Store──► MinIO                          │
│                       │                                                │
│                       │ 3. Trigger                                     │
│                       ▼                                                │
│                    Temporal ◄──4. Poll── Worker                        │
│                                           │                            │
│                                           │ 5. Retrieve                │
│                                           ▼                            │
│                                         MinIO                          │
│                                           │                            │
│                                           │ 6. Extract                 │
│                                           ▼                            │
│                                       Anthropic                        │
│                                           │                            │
│                                           │ 7. Assemble                │
│                                           ▼                            │
│                                         MinIO ──8. Publish──► User    │
└────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Document Status Lifecycle

```
CAPTURED → REGISTERED → ASSEMBLY_SPECIFICATION_IDENTIFIED → EXTRACTED → ASSEMBLED → PUBLISHED
                                                                              ↓
                                                                           FAILED
```

---

## 8. Technology Stack Summary

| Layer | Technology | C4 Abstraction |
|-------|------------|----------------|
| **Web Framework** | FastAPI, Uvicorn | Container (API) |
| **Workflow Engine** | Temporal | External System / Container |
| **Object Storage** | MinIO (S3-compatible) | Container |
| **AI/ML** | Anthropic SDK | External System |
| **Data Validation** | Pydantic 2.0+ | Code |
| **Type Safety** | Python 3.11+, mypy | Code |
| **Documentation** | Sphinx + HCD extensions | Container |
| **Testing** | pytest, pytest-asyncio | Code |

---

## 9. Key File Locations by C4 Level

| C4 Level | Description | Key Locations |
|----------|-------------|---------------|
| **System** | Project definition | `README.md`, `pyproject.toml` |
| **Container** | Entry points | `api/app.py`, `worker.py`, `docs/hcd_api/app.py`, `docs/hcd_mcp/server.py` |
| **Component** | Domain and use cases | `domain/models/`, `domain/repositories/`, `domain/use_cases/` |
| **Code** | Implementations | `repositories/minio/`, `services/knowledge_service/`, `workflows/` |

---

## 10. Observations and Recommendations

### 10.1 Strengths

1. **Clean separation:** Domain layer is framework-agnostic; the same use cases work in API, Worker, and CLI contexts.

2. **Protocol-based design:** Repository and service protocols enable testing and flexibility.

3. **Temporal integration:** The proxy pattern ensures workflow determinism while preserving clean architecture.

4. **Composable accelerators:** Contrib modules follow consistent structure and can be composed.

### 10.2 C4 Alignment

The architecture maps well to C4:
- **System boundary** is clearly defined (Julee platform)
- **Containers** are distinct runtime units (API, Worker, MinIO, Documentation)
- **Components** follow clean architecture layers
- **Code** uses consistent patterns (protocols, dataclasses)

### 10.3 Diagram Opportunities

Recommended C4 diagrams for Julee:

1. **System Context:** Show Julee with Temporal, Anthropic, MinIO
2. **Container Diagram:** API, Worker, Object Store, Documentation System
3. **Component Diagram:** For API container (routers → deps → use cases → repos)
4. **Dynamic Diagram:** CEAP workflow sequence
5. **Deployment Diagram:** Kubernetes/Docker deployment topology

---

*Document created: 2025-12-19*
*Analysis based on C4 model semantics from [C4 Fundamentals](./c4_fundamentals.md)*
