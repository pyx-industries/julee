"""MCP Framework policy.

This policy requires MCP applications to use julee's MCP framework.

The julee MCP framework provides:
- Automatic tool generation from use cases
- Progressive disclosure resources
- Documentation derivation from domain layer
- Consistent dependency injection patterns

This policy enforces:
- MCP apps import from julee.core.infrastructure.mcp
- MCP apps call create_mcp_server()
- MCP apps have a context.py module for DI factories
"""

from julee.core.entities.policy import Policy
from julee.core.policies import register_policy

policy = register_policy(
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
        test_module="julee.core.policies.mcp_framework.test_compliance",
    )
)
