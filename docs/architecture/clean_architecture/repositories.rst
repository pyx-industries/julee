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

- ``DocumentRepository``
- ``AssemblyRepository``
- ``AssemblySpecificationRepository``
- ``KnowledgeServiceQueryRepository``
- ``KnowledgeServiceConfigRepository``

MinIO Implementations
---------------------

Production implementations using S3-compatible object storage:

- ``MinioDocumentRepository``
- ``MinioAssemblyRepository``
- ``MinioAssemblySpecificationRepository``
- ``MinioKnowledgeServiceQueryRepository``
- ``MinioKnowledgeServiceConfigRepository``

Memory Implementations
----------------------

In-memory implementations for testing:

- ``MemoryDocumentRepository``
- ``MemoryAssemblyRepository``
- ``MemoryAssemblySpecificationRepository``
- ``MemoryKnowledgeServiceQueryRepository``
- ``MemoryKnowledgeServiceConfigRepository``

These are volatile and unsuitable for production,
but useful as testing doubles in unit tests
that run fast and in parallel without external dependencies.

Implementing Repositories
-------------------------

Repository protocols can define any interface suitable for the domain.
For the common case of simple CRUD operations,
:py:class:`~julee.repositories.base.BaseRepository` provides a generic starting point:

.. code-block:: python

    class DocumentRepository(BaseRepository[Document], Protocol):
        pass

Implementation mixins handle technology-specific boilerplate:

- :py:class:`~julee.repositories.memory.base.MemoryRepositoryMixin` - in-memory storage
- :py:class:`~julee.integrations.minio.client.MinioRepositoryMixin` - S3-compatible storage

The :doc:`DI container <dependency_injection>` wires protocols to implementations at runtime.

