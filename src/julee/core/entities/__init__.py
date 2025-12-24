"""Domain models for the shared (core) accelerator.

These models represent the foundational code concepts that julee is built on.
Viewpoint accelerators (HCD, C4) project onto these concepts.

Meta-entities (Entity, UseCase, etc.) define what Clean Architecture artifacts
ARE - their docstrings serve as definitions for doctrine documentation.
"""

from julee.core.entities.bounded_context import BoundedContext, StructuralMarkers
from julee.core.entities.code_info import (
    BoundedContextInfo,
    ClassInfo,
    FieldInfo,
    MethodInfo,
    PipelineInfo,  # Backwards compatibility alias for Pipeline
)
from julee.core.entities.dependency_rule import DependencyRule
from julee.core.entities.entity import Entity
from julee.core.entities.evaluation import EvaluationResult
from julee.core.entities.pipeline import Pipeline
from julee.core.entities.pipeline_dispatch import PipelineDispatchItem

# Routing models
from julee.core.entities.pipeline_route import (
    Condition,
    FieldCondition,
    Operator,
    PipelineCondition,
    PipelineRoute,
    Route,
)
from julee.core.entities.pipeline_router import PipelineRouter
from julee.core.entities.repository_protocol import RepositoryProtocol
from julee.core.entities.request import Request
from julee.core.entities.response import Response
from julee.core.entities.service_protocol import ServiceProtocol
from julee.core.entities.use_case import UseCase

# Backwards compatibility aliases
MultiplexRouter = PipelineRouter

__all__ = [
    # Core models
    "BoundedContext",
    "BoundedContextInfo",
    "StructuralMarkers",
    # Supporting models
    "ClassInfo",
    "FieldInfo",
    "MethodInfo",
    "EvaluationResult",
    # Meta-entities (doctrine-defining models)
    "DependencyRule",
    "Entity",
    "Pipeline",
    "PipelineInfo",  # Backwards compatibility alias
    "RepositoryProtocol",
    "Request",
    "Response",
    "ServiceProtocol",
    "UseCase",
    # Routing models
    "Condition",
    "FieldCondition",
    "MultiplexRouter",
    "Operator",
    "PipelineCondition",
    "PipelineDispatchItem",
    "PipelineRoute",
    "PipelineRouter",
    "Route",
]
