"""Test Organization policy.

This policy requires julee solutions to organize tests consistently.

Consistent test organization enables:
- Predictable test discovery
- Parallel test execution
- Clear separation of unit/integration/e2e tests
- Shared fixtures via conftest.py

This policy enforces:
- Every bounded context has a tests/ directory
- tests/ directories have __init__.py
- Test files follow test_*.py naming
- Solution has pytest configuration in pyproject.toml
- Standard test markers are defined
"""

from julee.core.entities.policy import Policy
from julee.core.policies import register_policy

policy = register_policy(
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
        test_module="julee.core.policies.test_organization.test_compliance",
    )
)
