"""
Repository implementations and infrastructure.

This package contains concrete implementations of the repository interfaces
defined in julee.domain.repositories.

Implementation packages:
- memory: In-memory implementations for testing
- minio: MinIO-based implementations for production
- temporal: Temporal workflow proxy implementations

Import implementations using their full module paths, e.g.:
    from julee.repositories.memory import MemoryDocumentRepository
    from julee.repositories.minio.document import (
        MinioDocumentRepository,
    )
"""
