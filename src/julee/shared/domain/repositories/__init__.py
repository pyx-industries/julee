"""Shared repository protocols.

Defines the generic repository interface following clean architecture patterns.
"""

from julee.shared.domain.repositories.base import BaseRepository
from julee.shared.domain.repositories.bounded_context import BoundedContextRepository

__all__ = [
    "BaseRepository",
    "BoundedContextRepository",
]
