"""Repository adapters shared by every bounded context.

- ``memory``: the mixin the in-memory repositories are built from.
- ``file``: the mixin that writes one entity to one file.

These are implementations. The protocols they satisfy —
``RepositoryOf``, ``BaseRepository``, ``Deletable`` — are domain and
live in :mod:`julee.core.repositories.base`, so that a bounded
context's ``domain/repositories/`` never has to import an adapter.

Concrete repositories live in the bounded context that owns the entity.
"""
