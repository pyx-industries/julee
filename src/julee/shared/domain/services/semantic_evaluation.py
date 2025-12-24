"""Semantic evaluation service protocol.

Defines the interface for services that evaluate judgment-based
architectural rules. These are rules that cannot be tested
structurally and require semantic understanding.

Examples of semantic rules:
- "A docstring SHOULD describe business purpose"
- "A use case SHOULD have single responsibility"
- "Variable names SHOULD be meaningful"

Implementations may use various approaches:
- Rule-based heuristics (string length, pattern matching)
- AI/LLM evaluation
- Statistical analysis
- Human review workflows
"""

from typing import Protocol, runtime_checkable

from julee.shared.domain.models import EvaluationResult
from julee.shared.domain.use_cases.requests import (
    EvaluateDocstringQualityRequest,
    EvaluateMethodComplexityRequest,
    EvaluateNamingQualityRequest,
    EvaluateSingleResponsibilityRequest,
)


@runtime_checkable
class SemanticEvaluationService(Protocol):
    """Service for evaluating semantic/judgment-based architectural rules.

    This protocol defines the interface for evaluating aspects of code
    quality that require judgment rather than structural analysis.

    All methods are async to accommodate implementations that may need
    to make external calls (e.g., to an AI service).
    """

    async def evaluate_docstring_quality(
        self, request: EvaluateDocstringQualityRequest
    ) -> EvaluationResult:
        """Evaluate if a docstring adequately describes its subject.

        A good docstring should:
        - Describe the business purpose, not implementation
        - Be concise but informative
        - Not repeat the class/function name

        Args:
            request: Contains docstring and context to evaluate

        Returns:
            EvaluationResult with pass/fail, confidence, and explanation
        """
        ...

    async def evaluate_single_responsibility(
        self, request: EvaluateSingleResponsibilityRequest
    ) -> EvaluationResult:
        """Evaluate if a class appears to have a single responsibility.

        Single Responsibility Principle: A class should have one,
        and only one, reason to change.

        Indicators of violation:
        - Many unrelated methods
        - Mixed abstractions (e.g., business logic AND formatting)
        - Name contains "And" or "Manager" without clear domain meaning

        Args:
            request: Contains class info to evaluate

        Returns:
            EvaluationResult with assessment
        """
        ...

    async def evaluate_naming_quality(
        self, request: EvaluateNamingQualityRequest
    ) -> EvaluationResult:
        """Evaluate if a name is meaningful and appropriate.

        Good names should:
        - Be intention-revealing
        - Use domain vocabulary
        - Avoid abbreviations (except well-known ones)
        - Follow naming conventions for the kind

        Args:
            request: Contains name, kind, and context to evaluate

        Returns:
            EvaluationResult with assessment
        """
        ...

    async def evaluate_method_complexity(
        self, request: EvaluateMethodComplexityRequest
    ) -> EvaluationResult:
        """Evaluate if a method is too complex.

        Complexity indicators:
        - Deep nesting
        - Many branches
        - Long methods
        - Mixed abstraction levels

        Args:
            request: Contains method source and name to evaluate

        Returns:
            EvaluationResult with assessment
        """
        ...
