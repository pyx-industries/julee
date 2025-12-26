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

Entity Semantics:
    This service transforms code structure entities (ClassInfo, MethodInfo,
    FieldInfo) into evaluation entities (EvaluationResult). It is bound to
    multiple entity types, which is the defining characteristic of a service
    (as opposed to a repository, which is bound to a single entity type).
"""

from typing import Protocol, runtime_checkable

from julee.core.entities.code_info import ClassInfo, FieldInfo, MethodInfo
from julee.core.entities.evaluation import EvaluationResult


@runtime_checkable
class SemanticEvaluationService(Protocol):
    """Service for evaluating semantic/judgment-based architectural rules.

    This protocol defines the interface for evaluating aspects of code
    quality that require judgment rather than structural analysis.

    Transforms: ClassInfo, MethodInfo, FieldInfo → EvaluationResult

    All methods are async to accommodate implementations that may need
    to make external calls (e.g., to an AI service).
    """

    async def evaluate_class_docstring(
        self, class_info: ClassInfo
    ) -> EvaluationResult:
        """Evaluate if a class docstring adequately describes its purpose.

        A good docstring should:
        - Describe the business purpose, not implementation
        - Be concise but informative
        - Not repeat the class name

        Args:
            class_info: The class to evaluate

        Returns:
            EvaluationResult with pass/fail, confidence, and explanation
        """
        ...

    async def evaluate_method_docstring(
        self, method_info: MethodInfo
    ) -> EvaluationResult:
        """Evaluate if a method docstring adequately describes its purpose.

        A good docstring should:
        - Describe what the method does, not how
        - Document parameters and return values
        - Be concise but informative

        Args:
            method_info: The method to evaluate

        Returns:
            EvaluationResult with pass/fail, confidence, and explanation
        """
        ...

    async def evaluate_single_responsibility(
        self, class_info: ClassInfo
    ) -> EvaluationResult:
        """Evaluate if a class has a single responsibility.

        Single Responsibility Principle: A class should have one,
        and only one, reason to change.

        Indicators of violation:
        - Many unrelated methods
        - Mixed abstractions (e.g., business logic AND formatting)
        - Name contains "And" or "Manager" without clear domain meaning

        Args:
            class_info: The class to evaluate

        Returns:
            EvaluationResult with assessment
        """
        ...

    async def evaluate_class_naming(
        self, class_info: ClassInfo
    ) -> EvaluationResult:
        """Evaluate if a class name is meaningful and appropriate.

        Good class names should:
        - Be intention-revealing
        - Use domain vocabulary
        - Follow naming conventions (PascalCase)
        - Reflect the class's single responsibility

        Args:
            class_info: The class to evaluate

        Returns:
            EvaluationResult with assessment
        """
        ...

    async def evaluate_method_naming(
        self, method_info: MethodInfo
    ) -> EvaluationResult:
        """Evaluate if a method name is meaningful and appropriate.

        Good method names should:
        - Be intention-revealing (verb phrases)
        - Use domain vocabulary
        - Follow naming conventions (snake_case)
        - Reflect what the method does

        Args:
            method_info: The method to evaluate

        Returns:
            EvaluationResult with assessment
        """
        ...

    async def evaluate_field_naming(
        self, field_info: FieldInfo
    ) -> EvaluationResult:
        """Evaluate if a field name is meaningful and appropriate.

        Good field names should:
        - Be intention-revealing
        - Use domain vocabulary
        - Follow naming conventions (snake_case)
        - Reflect the field's purpose

        Args:
            field_info: The field to evaluate

        Returns:
            EvaluationResult with assessment
        """
        ...

    async def evaluate_method_complexity(
        self, method_info: MethodInfo
    ) -> EvaluationResult:
        """Evaluate if a method is too complex.

        Complexity indicators:
        - Deep nesting
        - Many branches
        - Long methods
        - Mixed abstraction levels

        Requires method_info.source to be populated.

        Args:
            method_info: The method to evaluate (must have source)

        Returns:
            EvaluationResult with assessment
        """
        ...
