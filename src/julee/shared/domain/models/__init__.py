"""Domain models for the shared (core) accelerator.

These models represent the foundational code concepts that julee is built on.
Viewpoint accelerators (HCD, C4) project onto these concepts.
"""

from julee.shared.domain.models.bounded_context import BoundedContext, StructuralMarkers
from julee.shared.domain.models.code_info import (
    BoundedContextInfo,
    ClassInfo,
    FieldInfo,
    MethodInfo,
    PipelineInfo,
)
from julee.shared.domain.models.evaluation import EvaluationResult

__all__ = [
    "BoundedContext",
    "BoundedContextInfo",
    "ClassInfo",
    "EvaluationResult",
    "FieldInfo",
    "MethodInfo",
    "PipelineInfo",
    "StructuralMarkers",
]
