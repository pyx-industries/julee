"""Get effective policies use case.

Computes which policies apply to a solution based on its configuration.
"""

from pathlib import Path

from pydantic import BaseModel, Field

from julee.core.decorators import use_case
from julee.core.entities.policy import Policy, PolicyAdoption, SolutionPolicyConfig
from julee.core.repositories.policy import PolicyRepository
from julee.core.repositories.solution_config import SolutionConfigRepository
from julee.core.services.policy_adoption import PolicyAdoptionService


class GetEffectivePoliciesRequest(BaseModel):
    """Request for computing effective policies."""

    solution_root: Path = Field(description="Path to the solution root directory")

    model_config = {"arbitrary_types_allowed": True}


class GetEffectivePoliciesResponse(BaseModel):
    """Response containing effective policy adoptions."""

    config: SolutionPolicyConfig = Field(
        description="The solution's policy configuration"
    )
    adoptions: list[PolicyAdoption] = Field(description="All policy adoptions")
    policies_to_verify: list[Policy] = Field(
        description="Policies that should be verified"
    )
    skipped_policies: list[Policy] = Field(description="Policies that are skipped")

    model_config = {"arbitrary_types_allowed": True}


@use_case
class GetEffectivePoliciesUseCase:
    """Compute which policies apply to a solution.

    Reads the solution's configuration and determines which policies
    are in effect based on framework defaults, explicit adoptions,
    and explicit skips.
    """

    def __init__(
        self,
        solution_config_repository: SolutionConfigRepository,
        policy_repository: PolicyRepository,
        policy_adoption_service: PolicyAdoptionService,
    ) -> None:
        """Initialize with dependencies.

        Args:
            solution_config_repository: For reading solution configuration
            policy_repository: For accessing available policies
            policy_adoption_service: For computing effective policies
        """
        self.solution_config_repository = solution_config_repository
        self.policy_repository = policy_repository
        self.policy_adoption_service = policy_adoption_service

    async def execute(
        self, request: GetEffectivePoliciesRequest
    ) -> GetEffectivePoliciesResponse:
        """Execute the use case.

        Args:
            request: Request with solution path

        Returns:
            Response containing effective policies
        """
        # Get solution configuration
        config = await self.solution_config_repository.get_policy_config(
            request.solution_root
        )

        # Get all available policies
        all_policies = await self.policy_repository.list_policies()

        # Compute effective policies
        adoptions = self.policy_adoption_service.get_effective_policies(
            config, all_policies
        )

        # Get policies to verify vs skipped
        to_verify, skipped = self.policy_adoption_service.get_policies_to_verify(
            config, all_policies
        )

        return GetEffectivePoliciesResponse(
            config=config,
            adoptions=adoptions,
            policies_to_verify=to_verify,
            skipped_policies=skipped,
        )
