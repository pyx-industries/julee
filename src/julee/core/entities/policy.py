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

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Policy:
    """An adoptable strategic choice with compliance tests.

    Policies represent the "how" decisions in a julee solution. They are
    enforced only when adopted, either explicitly or through framework
    defaults.

    Attributes:
        slug: Unique identifier (e.g., "sphinx-documentation")
        name: Human-readable name (e.g., "Sphinx Documentation")
        description: What this policy requires and why
        framework_default: If True, applies to all julee solutions by default
        requires: Other policy slugs this policy depends on
        test_module: Dotted path to the compliance test module
    """

    slug: str
    name: str
    description: str
    framework_default: bool = False
    requires: tuple[str, ...] = field(default_factory=tuple)
    test_module: str = ""


@dataclass(frozen=True)
class PolicyAdoption:
    """A solution's adoption of a policy.

    Tracks which policies a solution has adopted and how (explicit
    adoption, framework default, or dependency).

    Attributes:
        policy_slug: The policy being adopted
        source: How this adoption came about
        skipped: If True, explicitly opted out of a framework default
    """

    policy_slug: str
    source: str  # "explicit", "framework_default", "dependency"
    skipped: bool = False


@dataclass(frozen=True)
class PolicyVerificationResult:
    """Result of verifying a policy's compliance.

    Attributes:
        policy_slug: The policy that was verified
        passed: Whether all compliance tests passed
        violations: List of violation messages if any
        skipped: If True, policy was not applicable (e.g., no Temporal usage)
        skip_reason: Why the policy was skipped
    """

    policy_slug: str
    passed: bool
    violations: tuple[str, ...] = field(default_factory=tuple)
    skipped: bool = False
    skip_reason: str = ""
