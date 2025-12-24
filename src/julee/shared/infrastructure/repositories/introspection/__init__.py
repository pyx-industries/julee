"""Introspection repositories.

Repository implementations that discover entities by inspecting the filesystem
and code structure, rather than persisting entities.
"""

from julee.shared.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)

__all__ = ["FilesystemBoundedContextRepository"]
