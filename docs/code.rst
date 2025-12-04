Code Structure
==============

This document describes the code organization of the Julee framework and how to structure your application.

Framework Code Structure
-------------------------

The Julee framework package structure::

    julee/
    ├── domain/
    │   ├── models/              # Domain entities
    │   │   ├── document/
    │   │   ├── assembly/
    │   │   ├── assembly_specification/
    │   │   ├── policy/
    │   │   └── knowledge_service_config/
    │   ├── repositories/        # Repository protocols
    │   │   ├── document.py
    │   │   ├── assembly.py
    │   │   └── ...
    │   └── use_cases/           # Business logic
    │       ├── extract_assemble_data.py
    │       ├── validate_document.py
    │       └── initialize_system_data.py
    ├── repositories/
    │   ├── minio/               # MinIO implementation
    │   │   ├── document.py
    │   │   ├── assembly.py
    │   │   └── client.py
    │   ├── memory/              # In-memory implementation
    │   │   ├── document.py
    │   │   └── ...
    │   └── temporal/            # Temporal activities
    │       └── activities.py
    ├── services/
    │   ├── knowledge_service/   # Service protocols & impls
    │   │   ├── knowledge_service.py      # Protocol
    │   │   ├── factory.py                # Factory
    │   │   ├── anthropic/
    │   │   │   └── knowledge_service.py  # Implementation
    │   │   └── memory/
    │   │       └── knowledge_service.py  # Test implementation
    │   └── temporal/            # Temporal utilities
    │       ├── activities.py
    │       └── proxies.py
    ├── workflows/               # CEAP workflow definitions
    │   ├── extract_assemble.py
    │   └── validate_document.py
    └── api/                     # API utilities (optional)
        ├── app.py
        ├── dependencies.py
        └── routers/

Your Application Structure
---------------------------

A typical Julee application::

    my_julee_app/
    ├── pyproject.toml           # julee as dependency
    ├── .env.example             # Environment template
    ├── docker-compose.yml       # Deployment configuration
    ├── my_app/
    │   ├── __init__.py
    │   ├── domain/
    │   │   ├── __init__.py
    │   │   └── models.py        # Your domain models
    │   ├── use_cases/           # Your use cases (optional)
    │   │   └── custom_logic.py
    │   ├── config.py            # Configuration
    │   ├── dependencies.py      # DI setup
    │   ├── worker.py            # Temporal worker
    │   └── api/                 # Your API (optional)
    │       ├── __init__.py
    │       ├── app.py
    │       └── routes.py
    └── tests/
        ├── test_domain.py
        ├── test_use_cases.py
        └── test_api.py

Domain Layer Organization
--------------------------

Models
~~~~~~

Domain models define your entities::

    # my_app/domain/models.py
    from pydantic import BaseModel, Field
    from datetime import datetime

    class Invoice(BaseModel):
        """Your domain model"""
        id: str
        number: str
        amount: float
        date: datetime
        customer_id: str

You can extend Julee's models or create your own::

    from julee.domain.models import Document

    class MyDocument(Document):
        """Extend Julee's Document"""
        custom_field: str

Repository Protocols
~~~~~~~~~~~~~~~~~~~~

Define if you need custom repositories::

    # my_app/domain/repositories.py
    from typing import Protocol
    from .models import Invoice

    class InvoiceRepository(Protocol):
        async def create(self, invoice: Invoice) -> Invoice: ...
        async def get(self, id: str) -> Invoice | None: ...
        async def list_by_customer(self, customer_id: str) -> list[Invoice]: ...

Use Cases
~~~~~~~~~

Your business logic::

    # my_app/use_cases/process_invoice.py
    from my_app.domain.models import Invoice
    from my_app.domain.repositories import InvoiceRepository
    from julee.services import KnowledgeService

    class ProcessInvoiceUseCase:
        def __init__(
            self,
            invoice_repo: InvoiceRepository,
            knowledge_service: KnowledgeService
        ):
            self.invoice_repo = invoice_repo
            self.knowledge_service = knowledge_service

        async def execute(self, invoice_id: str) -> dict:
            # Your business logic
            invoice = await self.invoice_repo.get(invoice_id)
            result = await self.knowledge_service.query(...)
            return result

Infrastructure Layer Organization
----------------------------------

Repository Implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~

Implement your repository protocols::

    # my_app/repositories/invoice.py
    from my_app.domain.models import Invoice
    from my_app.domain.repositories import InvoiceRepository
    from minio import Minio

    class MinioInvoiceRepository:
        def __init__(self, client: Minio):
            self.client = client
            self.bucket = "invoices"

        async def create(self, invoice: Invoice) -> Invoice:
            # Store in MinIO
            await self.client.put_object(...)
            return invoice

        async def get(self, id: str) -> Invoice | None:
            # Retrieve from MinIO
            data = await self.client.get_object(...)
            return Invoice(**data)

Service Implementations
~~~~~~~~~~~~~~~~~~~~~~~

Implement custom services if needed::

    # my_app/services/custom_service.py
    class MyCustomService:
        """Custom service logic"""
        def __init__(self, config: dict):
            self.config = config

        async def process(self, data: str) -> dict:
            # Your service logic
            pass

Configuration
-------------

Application Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

Centralize configuration::

    # my_app/config.py
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        # Application
        app_name: str = "my_julee_app"
        log_level: str = "INFO"

        # Storage
        minio_endpoint: str = "localhost:9000"
        minio_access_key: str
        minio_secret_key: str

        # Temporal
        temporal_endpoint: str = "localhost:7233"
        temporal_namespace: str = "default"

        # Services
        anthropic_api_key: str

        class Config:
            env_file = ".env"

    settings = Settings()

Dependency Injection Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~

Wire dependencies::

    # my_app/dependencies.py
    from fastapi import Depends
    from my_app.config import settings
    from my_app.repositories.invoice import MinioInvoiceRepository
    from julee.repositories.minio import MinioDocumentRepository
    from julee.services import KnowledgeServiceFactory
    from minio import Minio

    def get_minio_client() -> Minio:
        return Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False
        )

    def get_invoice_repository() -> InvoiceRepository:
        return MinioInvoiceRepository(get_minio_client())

    def get_document_repository() -> DocumentRepository:
        return MinioDocumentRepository(get_minio_client())

    def get_knowledge_service() -> KnowledgeService:
        factory = KnowledgeServiceFactory()
        return factory.create("anthropic", {
            "api_key": settings.anthropic_api_key,
            "model": "claude-3-5-sonnet-20241022"
        })

Application Entry Points
------------------------

Temporal Worker
~~~~~~~~~~~~~~~

Your worker runs Julee workflows::

    # my_app/worker.py
    import asyncio
    from temporalio.client import Client
    from temporalio.worker import Worker
    from julee.workflows import ExtractAssembleWorkflow, ValidateDocumentWorkflow
    from my_app.config import settings
    from my_app.dependencies import get_all_activities

    async def main():
        client = await Client.connect(settings.temporal_endpoint)

        worker = Worker(
            client,
            task_queue="my-app-queue",
            workflows=[
                ExtractAssembleWorkflow,
                ValidateDocumentWorkflow,
                # Your custom workflows
            ],
            activities=get_all_activities()
        )

        await worker.run()

    if __name__ == "__main__":
        asyncio.run(main())

API Application
~~~~~~~~~~~~~~~

Your API using Julee (optional)::

    # my_app/api/app.py
    from fastapi import FastAPI
    from my_app.api.routes import router

    app = FastAPI(title="My Julee App")
    app.include_router(router)

API Routes
~~~~~~~~~~

Your endpoints::

    # my_app/api/routes.py
    from fastapi import APIRouter, Depends
    from my_app.domain.models import Invoice
    from my_app.domain.repositories import InvoiceRepository
    from my_app.dependencies import get_invoice_repository

    router = APIRouter()

    @router.post("/invoices")
    async def create_invoice(
        invoice: Invoice,
        repo: InvoiceRepository = Depends(get_invoice_repository)
    ):
        return await repo.create(invoice)

    @router.get("/invoices/{invoice_id}")
    async def get_invoice(
        invoice_id: str,
        repo: InvoiceRepository = Depends(get_invoice_repository)
    ):
        return await repo.get(invoice_id)

Testing Structure
-----------------

Test Organization
~~~~~~~~~~~~~~~~~

Organize tests by layer::

    tests/
    ├── unit/
    │   ├── test_domain_models.py
    │   ├── test_use_cases.py
    │   └── test_repositories.py
    ├── integration/
    │   ├── test_workflows.py
    │   └── test_api.py
    └── conftest.py

Unit Tests
~~~~~~~~~~

Test with in-memory implementations::

    # tests/unit/test_use_cases.py
    import pytest
    from julee.repositories.memory import MemoryDocumentRepository
    from julee.services.knowledge_service.memory import MemoryKnowledgeService
    from my_app.use_cases import ProcessInvoiceUseCase

    @pytest.mark.asyncio
    async def test_process_invoice():
        # Use in-memory implementations
        doc_repo = MemoryDocumentRepository()
        knowledge = MemoryKnowledgeService()

        use_case = ProcessInvoiceUseCase(doc_repo, knowledge)
        result = await use_case.execute("invoice-123")

        assert result is not None

Integration Tests
~~~~~~~~~~~~~~~~~

Test with real infrastructure::

    # tests/integration/test_workflows.py
    import pytest
    from temporalio.testing import WorkflowEnvironment
    from julee.workflows import ExtractAssembleWorkflow

    @pytest.mark.asyncio
    async def test_extract_assemble_workflow():
        async with WorkflowEnvironment() as env:
            result = await env.client.execute_workflow(
                ExtractAssembleWorkflow.run,
                args=["doc-id", "spec-id"],
                id="test-workflow",
                task_queue="test-queue"
            )
            assert result["status"] == "completed"

Package Management
------------------

Dependencies
~~~~~~~~~~~~

Manage dependencies in ``pyproject.toml``::

    [project]
    name = "my-julee-app"
    version = "0.1.0"
    dependencies = [
        "julee>=0.1.0",
        # Your additional dependencies
    ]

    [project.optional-dependencies]
    dev = [
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
    ]

Development Workflow
~~~~~~~~~~~~~~~~~~~~

Install in development mode::

    pip install -e ".[dev]"

Code Quality
------------

Linting and Formatting
~~~~~~~~~~~~~~~~~~~~~~

Use ruff for linting and formatting::

    # pyproject.toml
    [tool.ruff]
    line-length = 88
    target-version = "py310"

    [tool.ruff.lint]
    select = ["E", "F", "I", "B", "C4", "UP"]

Type Checking
~~~~~~~~~~~~~

Use mypy for type checking::

    # pyproject.toml
    [tool.mypy]
    python_version = "3.10"
    warn_return_any = true
    disallow_untyped_defs = false
    check_untyped_defs = true

Pre-commit Hooks
~~~~~~~~~~~~~~~~

Automate quality checks::

    # .pre-commit-config.yaml
    repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.1.0
      hooks:
      - id: ruff
      - id: ruff-format

Documentation
~~~~~~~~~~~~~

Document your code::

    # Use docstrings
    def process_invoice(invoice_id: str) -> dict:
        """Process an invoice through the CEAP workflow.

        Args:
            invoice_id: The unique identifier for the invoice

        Returns:
            Dictionary containing processing results

        Raises:
            InvoiceNotFoundError: If invoice doesn't exist
        """
        pass

Best Practices
--------------

Module Organization
~~~~~~~~~~~~~~~~~~~

- One class per file (for large classes)
- Group related functionality
- Keep modules focused and cohesive

Naming Conventions
~~~~~~~~~~~~~~~~~~

- Classes: ``PascalCase``
- Functions/methods: ``snake_case``
- Constants: ``UPPER_SNAKE_CASE``
- Private: prefix with ``_``

Import Organization
~~~~~~~~~~~~~~~~~~~

::

    # Standard library
    import asyncio
    from datetime import datetime

    # Third-party
    from fastapi import FastAPI
    from pydantic import BaseModel

    # Julee framework
    from julee.domain.models import Document
    from julee.workflows import ExtractAssembleWorkflow

    # Your application
    from my_app.domain.models import Invoice
    from my_app.config import settings

Error Handling
~~~~~~~~~~~~~~

Use custom exceptions::

    # my_app/exceptions.py
    class InvoiceError(Exception):
        """Base exception for invoice operations"""
        pass

    class InvoiceNotFoundError(InvoiceError):
        """Invoice not found"""
        pass

Logging
~~~~~~~

Use structured logging::

    import logging

    logger = logging.getLogger(__name__)

    logger.info(
        "Processing invoice",
        extra={"invoice_id": invoice_id, "status": "started"}
    )
