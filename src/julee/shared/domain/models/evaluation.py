"""Semantic evaluation models.

Models for representing results of judgment-based architectural evaluations.
Used by SemanticEvaluationService to report on aspects of code quality
that cannot be tested structurally.
"""

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """Result of a semantic evaluation.

    Represents the outcome of an evaluation that requires judgment,
    such as assessing docstring quality or naming appropriateness.

    The `confidence` field indicates how certain the evaluator is
    about its assessment, where 1.0 is absolute certainty.
    """

    passed: bool
    """Whether the evaluation passed."""

    confidence: float = Field(ge=0.0, le=1.0)
    """Confidence level of the assessment (0.0 to 1.0)."""

    explanation: str
    """Human-readable explanation of the evaluation result."""

    suggestions: list[str] = Field(default_factory=list)
    """Optional suggestions for improvement if evaluation failed."""
