Configuration
=============

Environment Variables
---------------------

Core Settings
~~~~~~~~~~~~~

``ANTHROPIC_API_KEY``
    API key for Anthropic services.
    Required for knowledge service operations.

``TEMPORAL_ENDPOINT``
    Temporal server endpoint.
    Default: ``localhost:7233``

``MINIO_ENDPOINT``
    MinIO storage endpoint.
    Default: ``localhost:9000``

``LOG_LEVEL``
    Logging level for the application.
    Options: ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``
    Default: ``INFO``

``LOG_FORMAT``
    Python logging format string.
    Default: ``%(asctime)s - %(name)s - %(levelname)s - %(message)s``

Knowledge Service Configuration
--------------------------------

Knowledge services are configured through the API or during system initialization.

Service Types
~~~~~~~~~~~~~

Anthropic
^^^^^^^^^

Configuration options::

    {
      "service_type": "anthropic",
      "config": {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4096,
        "temperature": 1.0
      }
    }

Repository Configuration
------------------------

MinIO Storage
~~~~~~~~~~~~~

The system uses MinIO for object storage. Configuration is managed through environment variables:

- Endpoint: ``MINIO_ENDPOINT``
- Credentials: Currently hardcoded as ``minioadmin:minioadmin`` (development only)

Buckets are automatically created on initialization:

- ``assembly-specifications``
- ``documents``
- ``assemblies``
- ``knowledge-service-configs``
- ``knowledge-service-queries``
- ``policies``
- ``document-policy-validations``

Temporal Configuration
----------------------

Worker Settings
~~~~~~~~~~~~~~~

Workers connect to Temporal using the ``TEMPORAL_ENDPOINT`` environment variable.

Task Queue: ``julee-extract-assemble-queue``

Data Converter
~~~~~~~~~~~~~~

The system uses a custom Pydantic v2 compatible data converter for serializing workflow data.

Workflow Configuration
~~~~~~~~~~~~~~~~~~~~~~

Workflows are registered with the worker:

- ``ExtractAssembleWorkflow``
- ``ValidateDocumentWorkflow``

System Initialization
---------------------

On startup, the API server initializes:

1. Creates required MinIO buckets
2. Loads demo data (if configured)
3. Verifies knowledge service configurations

Docker Configuration
--------------------

The Docker Compose setup includes environment variable configuration for all services.

See ``.env.example`` for a template configuration file.
