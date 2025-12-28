"""Doctrine model for architectural rules extracted from tests.

Doctrine represents axiomatic, universal rules that define WHAT things are.
Unlike Policy (strategic choices), Doctrine is non-negotiable - violations
are always bugs.

The key insight: **Tests ARE the doctrine**. The test docstring states the
rule ("A bounded context MUST have entities/"), the test assertion enforces
it. This entity is a projection of those tests, not a separate source of
truth.

The extraction flow:
1. DoctrineRepository reads test_*.py files via AST
2. Test class docstring → DoctrineCategory description
3. Test method docstring → DoctrineRule statement
4. The test file name maps to an entity type (test_bounded_context.py → BoundedContext)

This preserves the single-source-of-truth principle while enabling
introspection, display, and cross-referencing of doctrine rules.
"""

from pathlib import Path

from pydantic import BaseModel, Field


class DoctrineRule(BaseModel, frozen=True):
    """A single doctrine rule extracted from a test method.

    Each rule corresponds to exactly one test. The test docstring IS the
    rule statement - if you change the docstring, you change the rule.
    The test assertion enforces the rule.
    """

    statement: str = Field(description="The rule text (from test method docstring)")
    test_name: str = Field(description="The test method name")
    test_file: Path = Field(description="Path to the test file")
    category: str = Field(description="Category within the area (from TestClass name)")
    area: str = Field(description="The entity type this rule applies to")

    model_config = {"arbitrary_types_allowed": True}

    @property
    def first_line(self) -> str:
        """Get the first line of the statement for brief display."""
        return self.statement.split("\n")[0].strip()


class DoctrineCategory(BaseModel, frozen=True):
    """A category of related doctrine rules within an area.

    Categories group rules by aspect. For example, BoundedContext doctrine
    might have categories like "Structure", "Naming", "Dependencies".
    Each category corresponds to a TestClass in the doctrine test file.
    """

    name: str = Field(description="Category name (from TestClass name)")
    description: str = Field(description="What this category covers (from TestClass docstring)")
    rules: tuple[DoctrineRule, ...] = Field(default_factory=tuple)

    @property
    def rule_count(self) -> int:
        """Number of rules in this category."""
        return len(self.rules)


class DoctrineArea(BaseModel, frozen=True):
    """A doctrine area covering rules for one entity type.

    Each area corresponds to an entity in julee.core.entities. The entity's
    docstring provides the definition of WHAT that entity is; the doctrine
    rules specify the constraints that instances must satisfy.

    For example:
    - Area: "Bounded Context"
    - Definition: From BoundedContext class docstring
    - Rules: From test_bounded_context.py test docstrings
    """

    name: str = Field(description="Human-readable area name")
    slug: str = Field(description="Machine-readable identifier")
    definition: str = Field(description="What this entity type IS (from entity docstring)")
    categories: tuple[DoctrineCategory, ...] = Field(default_factory=tuple)

    @property
    def all_rules(self) -> list[DoctrineRule]:
        """Get all rules from all categories."""
        return [rule for cat in self.categories for rule in cat.rules]

    @property
    def rule_count(self) -> int:
        """Total number of rules in this area."""
        return sum(cat.rule_count for cat in self.categories)


class DoctrineVerificationResult(BaseModel, frozen=True):
    """Result of verifying a single doctrine rule."""

    rule: DoctrineRule
    passed: bool = Field(description="Whether the test passed")
    error_message: str | None = Field(default=None, description="Failure message if failed")


class DoctrineVerificationReport(BaseModel, frozen=True):
    """Complete report from verifying doctrine compliance."""

    target: Path = Field(description="Path to the solution that was verified")
    results: tuple[DoctrineVerificationResult, ...] = Field(default_factory=tuple)
    scope: str = Field(default="all", description="What was verified")

    model_config = {"arbitrary_types_allowed": True}

    @property
    def passed(self) -> bool:
        """True if all rules passed."""
        return all(r.passed for r in self.results)

    @property
    def pass_count(self) -> int:
        """Number of rules that passed."""
        return sum(1 for r in self.results if r.passed)

    @property
    def fail_count(self) -> int:
        """Number of rules that failed."""
        return sum(1 for r in self.results if not r.passed)

    @property
    def failures(self) -> list[DoctrineVerificationResult]:
        """Get only the failed results."""
        return [r for r in self.results if not r.passed]
