"""Shared domain layer infrastructure.

Provides base protocols, models, and use cases for the core accelerator.
"""

from julee.shared.domain.models import BoundedContext, StructuralMarkers
from julee.shared.domain.repositories import BaseRepository, BoundedContextRepository
from julee.shared.domain.use_cases import (
    ListBoundedContextsRequest,
    ListBoundedContextsResponse,
    ListBoundedContextsUseCase,
)

__all__ = [
    # Models
    "BoundedContext",
    "StructuralMarkers",
    # Repositories
    "BaseRepository",
    "BoundedContextRepository",
    # Use cases
    "ListBoundedContextsUseCase",
    "ListBoundedContextsRequest",
    "ListBoundedContextsResponse",
]
