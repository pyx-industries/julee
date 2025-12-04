Deployment Architecture
=======================

This document describes the runtime deployment architecture of Julee applications using C4 diagrams.

C4 Context Diagram
------------------

A deployed Julee application with its service dependencies:

.. uml::

   @startuml
   !include <C4/C4_Context>

   Person(user, "User", "Application end user")
   System(juleeApp, "Julee Application", "Your app built with Julee framework")

   System_Boundary(services, "Services") {
       System_Ext(temporal, "Temporal", "Workflow orchestration service")
       System_Ext(storage, "Object Storage", "S3/MinIO storage service")
       System_Ext(external, "External Services", "Knowledge, AI, policy services, etc")
   }

   Rel(user, juleeApp, "Uses", "HTTPS")
   Rel(juleeApp, temporal, "Orchestrates workflows", "gRPC")
   Rel(juleeApp, storage, "Stores/retrieves data", "S3 API")
   Rel(juleeApp, external, "Calls services", "HTTPS/API")

   note right of services
     Services can be:
     - Third-party APIs (Anthropic)
     - Self-hosted (MinIO, Temporal)
     - Bundled with app
   end note
   @enduml

C4 Container Diagram
--------------------

Runtime containers in a typical Julee application deployment:

.. uml::

   @startuml
   !include <C4/C4_Container>

   Person(user, "User")

   System_Boundary(app, "Julee Application") {
       Container(ui, "Web UI", "React/Vue/etc", "Optional user interface")
       Container(api, "API Server", "FastAPI + Julee", "Application API using Julee")
       Container(worker, "Temporal Worker", "Python + Julee", "Runs Julee CEAP workflows")
   }

   System_Boundary(infra, "Infrastructure Services") {
       ContainerDb(temporal, "Temporal Server", "Workflow Engine", "Orchestrates CEAP workflows")
       ContainerDb(storage, "Object Storage", "MinIO/S3", "Document and data storage")
       ContainerDb(tempdb, "PostgreSQL", "Database", "Temporal persistence")
   }

   System_Ext(external, "External Services", "Knowledge, AI, policy services, etc.")

   Rel(user, ui, "Uses", "HTTPS")
   Rel(ui, api, "Calls", "HTTPS/JSON")
   Rel(api, temporal, "Starts workflows", "gRPC")
   Rel(worker, temporal, "Polls for work", "gRPC")
   Rel(api, storage, "Stores/retrieves", "S3 API")
   Rel(worker, storage, "Stores/retrieves", "S3 API")
   Rel(worker, external, "Calls services", "HTTPS/API")
   Rel(temporal, tempdb, "Persists", "SQL")
   @enduml

Container Responsibilities
---------------------------

**Web UI** (Optional)
    - User interface for your application
    - Built with any framework (React, Vue, etc.)
    - Calls the API Server

**API Server**
    - FastAPI application using Julee
    - REST endpoints for your domain
    - Triggers workflows via Temporal
    - Direct use case execution for synchronous operations
    - Manages authentication and authorization

**Temporal Worker**
    - Python process using Julee
    - Runs CEAP workflows
    - Executes use cases
    - Polls Temporal for work
    - Calls external services
    - Accesses storage via repositories

**Temporal Server** (Infrastructure)
    - Workflow orchestration engine
    - Manages workflow state
    - Handles retries and error recovery
    - Provides durability guarantees

**Object Storage** (Infrastructure)
    - MinIO or S3
    - Stores documents and metadata
    - Accessed via repository implementations

**PostgreSQL** (Infrastructure)
    - Temporal's persistence layer
    - Stores workflow execution history

**External Services** (Supply Chain)
    - Knowledge extraction (Anthropic, OpenAI)
    - Validation services
    - Notification services
    - Any other service your app needs

C4 Component Diagram
--------------------

Framework components and your application:

.. uml::

   @startuml
   !include <C4/C4_Component>

   Container_Boundary(framework, "Julee Framework") {
       Component(domain, "Domain", "Models & Protocols", "Entities, Repository Protocols, Service Protocols")
       Component(usecases, "Use Cases", "Business Logic", "CEAP use case implementations")
       Component(workflows, "CEAP Workflows", "Temporal workflows", "ExtractAssemble, Validate workflows")
       Component(repos, "Repository Impls", "Storage", "MinIO, Memory implementations")
       Component(services, "Service Impls", "Integrations", "Knowledge service implementations")
       Component(di, "DI Container", "FastAPI Depends", "Dependency injection and configuration")
   }

   Container_Boundary(app, "Your Application") {
       Component(appDomain, "Domain Models", "Pydantic", "Your business entities")
       Component(appUseCases, "Use Cases", "Business Logic", "Your application use cases")
       Component(appConfig, "Configuration", "Settings", "Service configuration, DI setup")
       Component(appAPI, "API Container", "FastAPI", "REST API, triggers workflows")
       Component(appWorker, "Worker Container", "Temporal", "Runs workflows, executes use cases")
   }

   Rel(appDomain, domain, "Extends/Uses")
   Rel(appUseCases, usecases, "Extends/Uses")
   Rel(appUseCases, domain, "Uses")
   Rel(appWorker, workflows, "Runs")
   Rel(workflows, appUseCases, "Calls")
   Rel(workflows, usecases, "Calls")
   Rel(usecases, domain, "Uses")
   Rel(usecases, repos, "Via protocols")
   Rel(usecases, services, "Via protocols")
   Rel(appAPI, appUseCases, "Calls")
   Rel(appAPI, workflows, "Triggers (via Temporal)")
   Rel(appConfig, di, "Configures")
   Rel(di, repos, "Provides")
   Rel(di, services, "Provides")
   @enduml

Data Flow: CEAP Workflow Execution
-----------------------------------

How a CEAP workflow executes:

.. uml::

   @startuml
   participant "API/Trigger" as api
   participant "Temporal" as temporal
   participant "Worker\n(Julee App)" as worker
   participant "Use Case" as usecase
   participant "Repository\n(via Protocol)" as repo
   participant "Service\n(via Protocol)" as service
   participant "Storage" as storage
   participant "External Service" as external

   api -> temporal: Start ExtractAssembleWorkflow
   temporal -> worker: Execute workflow
   worker -> usecase: execute_extract_assemble()

   usecase -> repo: get_document(id)
   repo -> storage: fetch document
   storage --> repo: document data
   repo --> usecase: Document

   usecase -> repo: get_specification(id)
   repo -> storage: fetch spec
   storage --> repo: spec data
   repo --> usecase: AssemblySpecification

   usecase -> service: query(content, prompts)
   service -> external: API call
   external --> service: extracted data
   service --> usecase: extraction results

   usecase -> usecase: assemble_data()

   usecase -> repo: create_assembly(assembly)
   repo -> storage: store assembly
   storage --> repo: saved
   repo --> usecase: Assembly

   usecase --> worker: result
   worker --> temporal: workflow complete
   temporal --> api: result
   @enduml

Deployment Patterns
-------------------

Single Server Deployment
~~~~~~~~~~~~~~~~~~~~~~~~

All containers on one machine (development/small deployments)::

    Docker Compose:
    - API Server
    - Worker
    - Temporal Server
    - MinIO
    - PostgreSQL
    - UI (optional)

Suitable for:

- Development
- Proof of concepts
- Small production workloads

Multi-Server Deployment
~~~~~~~~~~~~~~~~~~~~~~~

Containers distributed across multiple servers::

    API Tier:
    - Multiple API server instances
    - Load balancer

    Worker Tier:
    - Multiple worker instances
    - Auto-scaling based on queue depth

    Infrastructure Tier:
    - Temporal cluster
    - MinIO/S3
    - PostgreSQL cluster

Suitable for:

- Production workloads
- High availability requirements
- Horizontal scaling needs

Kubernetes Deployment
~~~~~~~~~~~~~~~~~~~~~

Container orchestration with Kubernetes::

    Deployments:
    - api-server (replicas: N)
    - worker (replicas: N)
    - temporal (StatefulSet)
    - minio (StatefulSet)
    - postgres (StatefulSet)

    Services:
    - api-service (LoadBalancer)
    - temporal-service (ClusterIP)
    - minio-service (ClusterIP)

Suitable for:

- Large-scale production
- Multi-tenancy
- Complex orchestration needs

Configuration Management
------------------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Configure services via environment variables::

    # Storage
    MINIO_ENDPOINT=minio:9000
    MINIO_ACCESS_KEY=minioadmin
    MINIO_SECRET_KEY=minioadmin

    # Temporal
    TEMPORAL_ENDPOINT=temporal:7233
    TEMPORAL_NAMESPACE=default

    # Services
    ANTHROPIC_API_KEY=sk-...

    # Application
    LOG_LEVEL=INFO

Configuration Files
~~~~~~~~~~~~~~~~~~~

Use configuration files for complex settings::

    # config.yaml
    repositories:
      document:
        type: minio
        bucket: documents
      assembly:
        type: minio
        bucket: assemblies

    services:
      knowledge:
        type: anthropic
        model: claude-3-5-sonnet-20241022
        max_tokens: 4096

Secrets Management
~~~~~~~~~~~~~~~~~~

Use proper secrets management:

- **Development**: ``.env`` files
- **Production**: Kubernetes Secrets, AWS Secrets Manager, HashiCorp Vault

Monitoring and Observability
-----------------------------

Metrics
~~~~~~~

Monitor application health:

- Workflow execution rates
- Workflow success/failure rates
- API response times
- Queue depths
- Resource utilization

Logging
~~~~~~~

Structured logging:

- Application logs (JSON format)
- Workflow execution logs
- Service call logs
- Error traces

Tracing
~~~~~~~

Distributed tracing:

- Temporal workflow traces
- API request traces
- Service call traces
- End-to-end transaction tracing

Health Checks
~~~~~~~~~~~~~

Implement health endpoints:

- ``/health``: Basic liveness check
- ``/ready``: Readiness check (dependencies)
- ``/metrics``: Prometheus metrics

Scaling Considerations
----------------------

API Server Scaling
~~~~~~~~~~~~~~~~~~

- Stateless, scale horizontally
- Load balance across instances
- Auto-scale based on CPU/memory

Worker Scaling
~~~~~~~~~~~~~~

- Scale based on queue depth
- One worker pool per task queue
- Consider resource limits per workflow

Storage Scaling
~~~~~~~~~~~~~~~

- MinIO/S3 scales independently
- Consider bucket partitioning
- Implement lifecycle policies

Temporal Scaling
~~~~~~~~~~~~~~~~

- Temporal handles workflow orchestration
- Scale Temporal cluster independently
- Monitor workflow execution capacity

Security Considerations
-----------------------

Network Security
~~~~~~~~~~~~~~~~

- TLS for all external communication
- VPC/network isolation
- Firewall rules
- API authentication (JWT, OAuth)

Data Security
~~~~~~~~~~~~~

- Encryption at rest (MinIO/S3)
- Encryption in transit (TLS)
- Access control (IAM, RBAC)
- Audit logging

Secrets
~~~~~~~

- Never commit secrets to code
- Use environment variables or secret managers
- Rotate secrets regularly
- Principle of least privilege

Backup and Disaster Recovery
-----------------------------

Backup Strategy
~~~~~~~~~~~~~~~

- Object storage (MinIO/S3): Regular snapshots
- Temporal database: Daily backups
- Configuration: Version control

Recovery Plan
~~~~~~~~~~~~~

- Document recovery procedures
- Test recovery regularly
- RTO/RPO requirements
- Failover procedures
