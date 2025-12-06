Deployment Architecture
=======================

This document describes the runtime deployment architecture of Julee applications using C4 diagrams.

C4 Context Diagram
------------------

A deployed Julee application with its dependencies:

.. uml:: diagrams/c4_context.puml

C4 Container Diagram
--------------------

Runtime containers in a typical Julee application deployment:

.. uml:: diagrams/c4_container.puml

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

.. uml:: diagrams/c4_component.puml

Data Flow: CEAP Workflow Execution
-----------------------------------

How a CEAP workflow executes:

.. uml:: diagrams/ceap_workflow_sequence.puml

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
