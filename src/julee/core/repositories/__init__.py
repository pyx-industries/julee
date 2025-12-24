"""Shared repository protocols.

Defines the generic repository interface following clean architecture patterns.
"""

from julee.core.repositories.base import BaseRepository
from julee.core.repositories.bounded_context import BoundedContextRepository
from julee.core.repositories.pipeline_route import (
    PipelineRouteRepository,
    RouteRepository,
)

__all__ = [
    "BaseRepository",
    "BoundedContextRepository",
    "PipelineRouteRepository",
    "RouteRepository",
]
