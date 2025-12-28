"""Sphinx Documentation policy.

This policy requires julee solutions to have buildable Sphinx documentation.

Documentation is not optional for production systems - it's essential for:
- Onboarding new team members
- Understanding system behavior
- API reference generation
- Architectural decision records

This policy enforces:
- docs/ directory exists
- conf.py (Sphinx configuration) exists
- Makefile with 'html' target exists
- Documentation is buildable with 'make html'
"""

from julee.core.entities.policy import Policy
from julee.core.policies import register_policy

policy = register_policy(
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
        test_module="julee.core.policies.sphinx_documentation.test_compliance",
    )
)
