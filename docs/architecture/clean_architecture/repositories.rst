Repositories
============

**Repositories store one entity each.**

A repository implements simple CRUD operations for one of
its bounded context's :doc:`entities`, abstracting storage technology.

Being bound to exactly one entity is the definition,
not a convention: a protocol bound to two or more is a
:doc:`service <services>`, and one bound to none is an
:doc:`oracle <oracles>`, a :doc:`calculator <calculators>`
or a :doc:`witness <witnesses>`.
:doc:`Protocols <protocols>` sets out all six.

Repositories are defined as :doc:`protocols`;
the :doc:`DI container <dependency_injection>` provides implementations.

A repository does I/O, so a :doc:`pipeline </architecture/solutions/pipelines>`
reaches it through a Temporal activity rather than calling it inline.

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

