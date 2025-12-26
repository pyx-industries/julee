"""Dependency injection for CEAP API.

Provides repository instances using Minio infrastructure.
The composition layer (apps/api/) can override via app.dependency_overrides.
"""

import logging
import os

from fastapi import Depends
from minio import Minio

from julee.contrib.ceap.infrastructure.repositories.minio.assembly_specification import (
    MinioAssemblySpecificationRepository,
)
from julee.contrib.ceap.infrastructure.repositories.minio.document import (
    MinioDocumentRepository,
)
from julee.contrib.ceap.infrastructure.repositories.minio.knowledge_service_config import (
    MinioKnowledgeServiceConfigRepository,
)
from julee.contrib.ceap.infrastructure.repositories.minio.knowledge_service_query import (
    MinioKnowledgeServiceQueryRepository,
)
from julee.contrib.ceap.repositories.assembly_specification import (
    AssemblySpecificationRepository,
)
from julee.contrib.ceap.repositories.document import DocumentRepository
from julee.contrib.ceap.repositories.knowledge_service_config import (
    KnowledgeServiceConfigRepository,
)
from julee.contrib.ceap.repositories.knowledge_service_query import (
    KnowledgeServiceQueryRepository,
)
from julee.core.infrastructure.repositories.minio.client import MinioClient

logger = logging.getLogger(__name__)

# Singleton minio client
_minio_client: MinioClient | None = None


def _get_minio_client() -> MinioClient:
    """Get or create Minio client singleton."""
    global _minio_client
    if _minio_client is None:
        endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
        access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
        secure = os.environ.get("MINIO_SECURE", "false").lower() == "true"

        _minio_client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
    return _minio_client  # type: ignore[return-value]


async def get_minio_client() -> MinioClient:
    """FastAPI dependency for Minio client."""
    return _get_minio_client()


async def get_assembly_specification_repository(
    minio_client: MinioClient = Depends(get_minio_client),
) -> AssemblySpecificationRepository:
    """FastAPI dependency for AssemblySpecificationRepository."""
    return MinioAssemblySpecificationRepository(client=minio_client)


async def get_document_repository(
    minio_client: MinioClient = Depends(get_minio_client),
) -> DocumentRepository:
    """FastAPI dependency for DocumentRepository."""
    return MinioDocumentRepository(client=minio_client)


async def get_knowledge_service_config_repository(
    minio_client: MinioClient = Depends(get_minio_client),
) -> KnowledgeServiceConfigRepository:
    """FastAPI dependency for KnowledgeServiceConfigRepository."""
    return MinioKnowledgeServiceConfigRepository(client=minio_client)


async def get_knowledge_service_query_repository(
    minio_client: MinioClient = Depends(get_minio_client),
) -> KnowledgeServiceQueryRepository:
    """FastAPI dependency for KnowledgeServiceQueryRepository."""
    return MinioKnowledgeServiceQueryRepository(client=minio_client)
