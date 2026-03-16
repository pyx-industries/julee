"""Policy model for adoptable strategic choices.

A Policy represents a strategic choice that solutions can adopt. Unlike
Doctrine (axiomatic, universal), Policies are opt-in decisions about
HOW to implement things rather than WHAT things are.

The distinction:
- Doctrine: "Entities MUST be PascalCase" (defines what an Entity IS)
- Policy: "Solutions should use Sphinx for documentation" (a choice)

Policies can be:
- Framework-default: Automatically apply to julee solutions (can opt out)
- Optional: Must be explicitly adopted

When a solution declares `[tool.julee]` in pyproject.toml, it becomes a
"julee solution" and inherits framework-default policies. These inherited
policies become doctrine for that solution - violations are bugs to fix.

Policy adoption is explicit:
```toml
[tool.julee]
policies = ["postgresql-patterns"]  # Opt into additional policies
skip_policies = ["temporal-pipelines"]  # Opt out of framework defaults
```
"""

from pydantic import BaseModel, Field


class Policy(BaseModel, frozen=True):
    """An adoptable strategic choice with compliance tests.

    Policies represent the "how" decisions in a julee solution. They are
    enforced only when adopted, either explicitly or through framework
    defaults.
    """

    slug: str = Field(description="Unique identifier (e.g., 'sphinx-documentation')")
    name: str = Field(description="Human-readable name")
    description: str = Field(description="What this policy requires and why")
    framework_default: bool = Field(
        default=False,
        description="If True, applies to all julee solutions by default",
    )
    requires: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Other policy slugs this policy depends on",
    )
    test_module: str = Field(
        default="",
        description="Dotted path to the compliance test module",
    )


class PolicyAdoption(BaseModel, frozen=True):
    """A solution's adoption of a policy.

    Tracks which policies a solution has adopted and how (explicit
    adoption, framework default, or dependency).
    """

    policy_slug: str = Field(description="The policy being adopted")
    source: str = Field(
        description="How adopted: 'explicit', 'framework_default', 'dependency'"
    )
    skipped: bool = Field(default=False, description="If True, explicitly opted out")


class PolicyVerificationResult(BaseModel, frozen=True):
    """Result of verifying a policy's compliance."""

    policy_slug: str = Field(description="The policy that was verified")
    passed: bool = Field(description="Whether all compliance tests passed")
    violations: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Violation messages if any",
    )
    skipped: bool = Field(
        default=False, description="If True, policy was not applicable"
    )
    skip_reason: str = Field(default="", description="Why the policy was skipped")


class SolutionPolicyConfig(BaseModel, frozen=True):
    """Policy configuration for a solution.

    Read from [tool.julee] in pyproject.toml. Presence of this section
    declares the project as a "julee solution" which inherits framework-default
    policies.

    Structure configuration allows solutions to customize where bounded contexts
    and documentation are located:

    ```toml
    [tool.julee]
    search_root = "src/acme"  # Where to find bounded contexts
    docs_root = "docs"        # Where to find documentation
    ```
    """

    is_julee_solution: bool = Field(
        default=False,
        description="True if [tool.julee] section exists",
    )
    policies: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Explicitly adopted policy slugs",
    )
    skip_policies: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Explicitly skipped policy slugs (framework defaults)",
    )
    search_root: str | None = Field(
        default=None,
        description="Root directory for bounded context discovery (relative to project root). "
        "Required for introspection features.",
    )
    docs_root: str | None = Field(
        default=None,
        description="Root directory for documentation (relative to project root). "
        "Required for HCD features.",
    )
