"""Shared repository protocols.

Defines the generic repository interface following clean architecture patterns.
"""

from julee.shared.repositories.base import BaseRepository
from julee.shared.repositories.bounded_context import BoundedContextRepository
from julee.shared.repositories.pipeline_route import (
    PipelineRouteRepository,
    RouteRepository,
)

__all__ = [
    "BaseRepository",
    "BoundedContextRepository",
    "PipelineRouteRepository",
    "RouteRepository",
]
