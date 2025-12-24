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

from pydantic import BaseModel, Field

from julee.core.entities import EvaluationResult


class EvaluateDocstringQualityRequest(BaseModel):
    """Request for evaluating docstring quality.

    Used by SemanticEvaluationService to assess whether a docstring
    adequately describes its subject.
    """

    docstring: str = Field(description="The docstring text to evaluate")
    context: str = Field(
        description="What the docstring describes (e.g., 'CreateInvoiceUseCase')"
    )


class EvaluateSingleResponsibilityRequest(BaseModel):
    """Request for evaluating single responsibility principle.

    Used by SemanticEvaluationService to assess whether a class
    has a single responsibility.
    """

    class_name: str = Field(description="Name of the class")
    class_docstring: str = Field(default="", description="Class docstring")
    method_names: list[str] = Field(
        default_factory=list, description="Names of public methods in the class"
    )
    field_names: list[str] = Field(
        default_factory=list, description="Names of fields/attributes in the class"
    )


class EvaluateNamingQualityRequest(BaseModel):
    """Request for evaluating naming quality.

    Used by SemanticEvaluationService to assess whether a name
    is meaningful and appropriate.
    """

    name: str = Field(description="The identifier name to evaluate")
    kind: str = Field(description="What it is: 'class', 'method', 'variable', 'field'")
    context: str = Field(
        default="", description="Surrounding context (class name, module, etc.)"
    )


class EvaluateMethodComplexityRequest(BaseModel):
    """Request for evaluating method complexity.

    Used by SemanticEvaluationService to assess whether a method
    is too complex.
    """

    method_source: str = Field(description="The method's source code")
    method_name: str = Field(description="The name of the method")


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
