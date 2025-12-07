Repositories
============

**Repositories store things.**
Not to be confused with :doc:`services`, which do things.

A repository implements simple CRUD operations for :doc:`entities`,
abstracting storage technology.

Repositories are defined as :doc:`protocols`;
the :doc:`DI container <dependency_injection>` provides implementations.

CEAP Repository Protocols
-------------------------

The CEAP :doc:`use case <use_cases>` depends on these repository protocols:

- :py:class:`julee.domain.repositories.DocumentRepository`
- :py:class:`julee.domain.repositories.AssemblyRepository`
- :py:class:`julee.domain.repositories.AssemblySpecificationRepository`
- :py:class:`julee.domain.repositories.KnowledgeServiceQueryRepository`
- :py:class:`julee.domain.repositories.KnowledgeServiceConfigRepository`

MinIO Implementations
---------------------

Production implementations using S3-compatible object storage:

- :py:class:`julee.repositories.minio.MinioDocumentRepository`
- :py:class:`julee.repositories.minio.MinioAssemblyRepository`
- :py:class:`julee.repositories.minio.MinioAssemblySpecificationRepository`
- :py:class:`julee.repositories.minio.MinioKnowledgeServiceQueryRepository`
- :py:class:`julee.repositories.minio.MinioKnowledgeServiceConfigRepository`

Memory Implementations
----------------------

In-memory implementations for testing:

- :py:class:`julee.repositories.memory.MemoryDocumentRepository`
- :py:class:`julee.repositories.memory.MemoryAssemblyRepository`
- :py:class:`julee.repositories.memory.MemoryAssemblySpecificationRepository`
- :py:class:`julee.repositories.memory.MemoryKnowledgeServiceQueryRepository`
- :py:class:`julee.repositories.memory.MemoryKnowledgeServiceConfigRepository`

These are volatile and unsuitable for production,
but useful as testing doubles in unit tests
that run fast and in parallel without external dependencies.

TODO:
* explain how repositories are implemented
* pydantic interfaces (pydantic)
  foo.domain.repositories.{the-thing}
* whatever technology
  foo.repositories.{the-tech}.{the-thing}
* dependency injection
  settings.py <- app-specific-DI-container.py <- app
  (maybe one day it's a generic DI container and everything is driven by settings)

