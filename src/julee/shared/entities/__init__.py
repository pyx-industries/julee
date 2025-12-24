"""Domain models for the shared (core) accelerator.

These models represent the foundational code concepts that julee is built on.
Viewpoint accelerators (HCD, C4) project onto these concepts.

Meta-entities (Entity, UseCase, etc.) define what Clean Architecture artifacts
ARE - their docstrings serve as definitions for doctrine documentation.
"""

from julee.shared.entities.bounded_context import BoundedContext, StructuralMarkers
from julee.shared.entities.code_info import (
    BoundedContextInfo,
    ClassInfo,
    FieldInfo,
    MethodInfo,
    PipelineInfo,  # Backwards compatibility alias for Pipeline
)
from julee.shared.entities.dependency_rule import DependencyRule
from julee.shared.entities.entity import Entity
from julee.shared.entities.evaluation import EvaluationResult
from julee.shared.entities.pipeline import Pipeline
from julee.shared.entities.pipeline_dispatch import PipelineDispatchItem

# Routing models
from julee.shared.entities.pipeline_route import (
    Condition,
    FieldCondition,
    Operator,
    PipelineCondition,
    PipelineRoute,
    Route,
)
from julee.shared.entities.pipeline_router import PipelineRouter
from julee.shared.entities.repository_protocol import RepositoryProtocol
from julee.shared.entities.request import Request
from julee.shared.entities.response import Response
from julee.shared.entities.service_protocol import ServiceProtocol
from julee.shared.entities.use_case import UseCase

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
