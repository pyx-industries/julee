"""Get policy use case.

Provides access to a single policy by slug.
"""

from pydantic import BaseModel, Field

from julee.core.decorators import use_case
from julee.core.entities.policy import Policy
from julee.core.repositories.policy import PolicyRepository


class GetPolicyRequest(BaseModel):
    """Request for getting a policy."""

    slug: str = Field(description="The policy slug to look up")


class GetPolicyResponse(BaseModel):
    """Response containing the policy if found."""

    policy: Policy | None = None

    model_config = {"arbitrary_types_allowed": True}


@use_case
class GetPolicyUseCase:
    """Get a policy by slug.

    Returns the policy if found, None otherwise.
    """

    def __init__(self, policy_repository: PolicyRepository) -> None:
        """Initialize with policy repository.

        Args:
            policy_repository: Repository for accessing policies
        """
        self.policy_repository = policy_repository

    async def execute(self, request: GetPolicyRequest) -> GetPolicyResponse:
        """Execute the use case.

        Args:
            request: Request with policy slug

        Returns:
            Response containing the policy if found
        """
        policy = await self.policy_repository.get_policy(request.slug)
        return GetPolicyResponse(policy=policy)
