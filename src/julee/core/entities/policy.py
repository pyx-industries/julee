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

from dataclasses import dataclass


@dataclass(frozen=True)
class Policy:
    """An adoptable strategic choice with compliance tests.

    Policies represent the "how" decisions in a julee solution. They are
    enforced only when adopted, either explicitly or through framework
    defaults.
    """

    slug: str
    """Unique identifier (e.g., 'sphinx-documentation')."""

    name: str
    """Human-readable name."""

    description: str
    """What this policy requires and why."""

    framework_default: bool = False
    """If True, applies to all julee solutions by default."""

    requires: tuple[str, ...] = ()
    """Other policy slugs this policy depends on."""

    test_module: str = ""
    """Dotted path to the compliance test module."""


@dataclass(frozen=True)
class PolicyAdoption:
    """A solution's adoption of a policy.

    Tracks which policies a solution has adopted and how (explicit
    adoption, framework default, or dependency).
    """

    policy_slug: str
    """The policy being adopted."""

    source: str
    """How it was adopted.

    One of 'explicit', 'framework_default' or 'dependency'.
    """

    skipped: bool = False
    """If True, explicitly opted out."""


@dataclass(frozen=True)
class PolicyVerificationResult:
    """Result of verifying a policy's compliance."""

    policy_slug: str
    """The policy that was verified."""

    passed: bool
    """Whether all compliance tests passed."""

    violations: tuple[str, ...] = ()
    """Violation messages if any."""

    skipped: bool = False
    """If True, policy was not applicable."""

    skip_reason: str = ""
    """Why the policy was skipped."""


@dataclass(frozen=True)
class SolutionPolicyConfig:
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
    kits = ["ceap"]           # Which installed kits this solution adopts
    composition_roots = ["apps"]  # Where this solution wires kits together
    ```
    """

    is_julee_solution: bool = False
    """True if [tool.julee] section exists."""

    policies: tuple[str, ...] = ()
    """Explicitly adopted policy slugs."""

    skip_policies: tuple[str, ...] = ()
    """Explicitly skipped policy slugs (framework defaults)."""

    kits: tuple[str, ...] = ()
    """Slugs of kits this solution adopts.

    Installing a kit does not activate it; adoption is explicit.
    """

    search_root: str | None = None
    """Root directory for bounded context discovery, relative to the
    project root. Required for introspection features."""

    docs_root: str | None = None
    """Root directory for documentation, relative to the project root.
    Required for HCD features."""

    bounded_contexts: str | None = None
    """Set to "none" by a codebase that deliberately has none.

    A framework, or a projection over kits. Doctrine objects to an
    undeclared emptiness, because a run with no subject passes every
    rule and reads exactly like a run over a codebase that complies.
    """

    composition_roots: tuple[str, ...] = ("apps",)
    """Directories, relative to search_root, where this solution wires
    kits together.

    Only these may import a kit's infrastructure; every other bounded
    context is held to what the kit offers. Defaults to apps/, which is
    where a composition root usually lives (ADR 010).
    """
