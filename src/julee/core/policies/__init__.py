"""Adoptable policies for julee solutions.

Policies represent strategic choices that solutions can adopt. Unlike
doctrine (axiomatic, universal), policies are opt-in.

Framework-default policies apply automatically to solutions that declare
`[tool.julee]` in pyproject.toml. Solutions can opt out explicitly.

Available policies:
- sphinx_documentation: Require Sphinx documentation
- test_organization: Require tests/ directories in bounded contexts
- mcp_framework: Require MCP apps to use julee's MCP framework
- temporal_pipelines: Require Temporal pipelines to follow julee patterns

Usage:
    from julee.core.policies import get_policy, list_policies
    from julee.core.policies import get_framework_default_policies
"""

from julee.core.entities.policy import Policy

# Registry of all available policies
_POLICY_REGISTRY: dict[str, Policy] = {}


def register_policy(policy: Policy) -> Policy:
    """Register a policy in the global registry."""
    _POLICY_REGISTRY[policy.slug] = policy
    return policy


def get_policy(slug: str) -> Policy | None:
    """Get a policy by slug."""
    return _POLICY_REGISTRY.get(slug)


def list_policies() -> list[Policy]:
    """List all registered policies."""
    return list(_POLICY_REGISTRY.values())


def get_framework_default_policies() -> list[Policy]:
    """Get policies that apply by default to julee solutions."""
    return [p for p in _POLICY_REGISTRY.values() if p.framework_default]


# Import policy modules to trigger registration
from julee.core.policies import sphinx_documentation  # noqa: E402, F401
from julee.core.policies import test_organization  # noqa: E402, F401
from julee.core.policies import mcp_framework  # noqa: E402, F401
from julee.core.policies import temporal_pipelines  # noqa: E402, F401
