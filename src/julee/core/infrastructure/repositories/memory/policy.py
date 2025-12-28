"""In-memory policy repository.

Defines and provides access to available policies.
Policy definitions are configuration - they live in infrastructure.
"""

from julee.core.entities.policy import Policy


# Policy definitions - configuration data
_POLICIES: list[Policy] = [
    Policy(
        slug="sphinx-documentation",
        name="Sphinx Documentation",
        description=(
            "Solutions must have buildable Sphinx documentation. "
            "This ensures consistent, professional documentation that "
            "can be built and deployed automatically."
        ),
        framework_default=True,
        requires=(),
        test_module="julee.core.infrastructure.policy_compliance.sphinx_documentation",
    ),
    Policy(
        slug="test-organization",
        name="Test Organization",
        description=(
            "Solutions must organize tests consistently with tests/ "
            "directories in bounded contexts, proper naming conventions, "
            "and pytest configuration in pyproject.toml."
        ),
        framework_default=True,
        requires=(),
        test_module="julee.core.infrastructure.policy_compliance.test_organization",
    ),
    Policy(
        slug="mcp-framework",
        name="MCP Framework",
        description=(
            "MCP applications must use julee's MCP framework for "
            "consistent tool generation, progressive disclosure, "
            "and documentation derivation from the domain layer."
        ),
        framework_default=True,
        requires=(),
        test_module="julee.core.infrastructure.policy_compliance.mcp_framework",
    ),
    Policy(
        slug="temporal-pipelines",
        name="Temporal Pipelines",
        description=(
            "Temporal workflows must follow julee's pipeline patterns, "
            "delegating to use cases for business logic and using proper "
            "Temporal decorators."
        ),
        framework_default=True,
        requires=(),
        test_module="julee.core.infrastructure.policy_compliance.temporal_pipelines",
    ),
    Policy(
        slug="no-reexports",
        name="No Re-exports",
        description=(
            "__init__.py files MUST NOT re-export symbols from other modules. "
            "Import directly from the defining module to maintain clear dependency graphs."
        ),
        framework_default=True,
        requires=(),
        test_module="julee.core.infrastructure.policy_compliance.no_reexports",
    ),
]

_POLICY_MAP: dict[str, Policy] = {p.slug: p for p in _POLICIES}


class RegistryPolicyRepository:
    """Policy repository with statically defined policies.

    Policies are defined as configuration in this module.
    No registration mechanism - just data.
    """

    async def list_policies(self) -> list[Policy]:
        """List all available policies."""
        return _POLICIES.copy()

    async def get_policy(self, slug: str) -> Policy | None:
        """Get a policy by slug."""
        return _POLICY_MAP.get(slug)

    async def get_framework_defaults(self) -> list[Policy]:
        """Get policies that apply by default to julee solutions."""
        return [p for p in _POLICIES if p.framework_default]
