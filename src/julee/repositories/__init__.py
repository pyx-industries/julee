"""Repository support shared by every bounded context.

- ``base``: ``RepositoryOf``, the marker that binds a repository to its
  entity, and ``BaseRepository``, the CRUD protocol built on it.
- ``memory``: the mixin the in-memory repositories are built from.

Concrete repositories live in the bounded context that owns the entity.
"""
