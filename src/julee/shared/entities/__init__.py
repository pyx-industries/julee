"""Domain models for the shared (core) accelerator.

These models represent the foundational code concepts that julee is built on.
Viewpoint accelerators (HCD, C4) project onto these concepts.

Meta-entities (Entity, UseCase, etc.) define what Clean Architecture artifacts
ARE - their docstrings serve as definitions for doctrine documentation.
"""

from julee.shared.domain.models.bounded_context import BoundedContext, StructuralMarkers
from julee.shared.domain.models.code_info import (
    BoundedContextInfo,
    ClassInfo,
    FieldInfo,
    MethodInfo,
    PipelineInfo,  # Backwards compatibility alias for Pipeline
)
from julee.shared.domain.models.dependency_rule import DependencyRule
from julee.shared.domain.models.entity import Entity
from julee.shared.domain.models.evaluation import EvaluationResult
from julee.shared.domain.models.pipeline import Pipeline
from julee.shared.domain.models.pipeline_dispatch import PipelineDispatchItem

# Routing models
from julee.shared.domain.models.pipeline_route import (
    Condition,
    FieldCondition,
    Operator,
    PipelineCondition,
    PipelineRoute,
    Route,
)
from julee.shared.domain.models.pipeline_router import PipelineRouter
from julee.shared.domain.models.repository_protocol import RepositoryProtocol
from julee.shared.domain.models.request import Request
from julee.shared.domain.models.response import Response
from julee.shared.domain.models.service_protocol import ServiceProtocol
from julee.shared.domain.models.use_case import UseCase

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
