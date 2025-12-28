"""List policies use case.

Provides access to available policies through the repository.
"""

from pydantic import BaseModel, Field

from julee.core.decorators import use_case
from julee.core.entities.policy import Policy
from julee.core.repositories.policy import PolicyRepository


class ListPoliciesRequest(BaseModel):
    """Request for listing policies."""

    framework_defaults_only: bool = Field(
        default=False,
        description="If True, only return framework-default policies",
    )


class ListPoliciesResponse(BaseModel):
    """Response containing available policies."""

    policies: list[Policy]

    model_config = {"arbitrary_types_allowed": True}


@use_case
class ListPoliciesUseCase:
    """List available policies.

    Returns all registered policies, optionally filtered to
    framework defaults only.
    """

    def __init__(self, policy_repository: PolicyRepository) -> None:
        """Initialize with policy repository.

        Args:
            policy_repository: Repository for accessing policies
        """
        self.policy_repository = policy_repository

    async def execute(self, request: ListPoliciesRequest) -> ListPoliciesResponse:
        """Execute the use case.

        Args:
            request: Request with optional filters

        Returns:
            Response containing matching policies
        """
        if request.framework_defaults_only:
            policies = await self.policy_repository.get_framework_defaults()
        else:
            policies = await self.policy_repository.list_policies()

        return ListPoliciesResponse(policies=policies)
