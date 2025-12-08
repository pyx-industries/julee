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

Implementing Repositories
-------------------------

Repository protocols can define any interface suitable for the domain.
For the common case of simple CRUD operations,
:py:class:`~julee.domain.repositories.BaseRepository` provides a generic starting point:

.. code-block:: python

    class DocumentRepository(BaseRepository[Document], Protocol):
        pass

Implementation mixins handle technology-specific boilerplate:

- :py:class:`~julee.repositories.memory.base.MemoryRepositoryMixin` - in-memory storage
- :py:class:`~julee.repositories.minio.client.MinioRepositoryMixin` - S3-compatible storage

The :doc:`DI container <dependency_injection>` wires protocols to implementations at runtime.

