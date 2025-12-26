"""Introspection repositories.

Repository implementations that discover entities by inspecting the filesystem
and code structure, rather than persisting entities.
"""

from julee.core.infrastructure.repositories.introspection.application import (
    FilesystemApplicationRepository,
)
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)
from julee.core.infrastructure.repositories.introspection.solution import (
    FilesystemSolutionRepository,
)

__all__ = [
    "FilesystemApplicationRepository",
    "FilesystemBoundedContextRepository",
    "FilesystemSolutionRepository",
]
