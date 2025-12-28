"""Temporal Pipelines policy.

This policy requires Temporal workflows to follow julee's pipeline patterns.

The pipeline pattern ensures:
- Separation of business logic (UseCase) from orchestration (Pipeline)
- Consistent workflow structure across the solution
- Proper use of Temporal decorators
- Delegation to use cases, not inline business logic

This policy enforces:
- Pipelines have @workflow.defn decorator
- Pipelines have run() method with @workflow.run decorator
- Pipelines delegate to UseCase.execute()
- Pipelines don't contain business logic directly
"""

from julee.core.entities.policy import Policy
from julee.core.policies import register_policy

policy = register_policy(
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
        test_module="julee.core.policies.temporal_pipelines.test_compliance",
    )
)
