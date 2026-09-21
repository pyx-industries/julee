"""Repository support shared by every bounded context.

- ``base``: the ``BaseRepository`` protocol.
- ``memory``: the mixin the in-memory repositories are built from.

Concrete repositories live in the bounded context that owns the entity.
"""
