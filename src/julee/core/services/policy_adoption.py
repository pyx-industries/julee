"""Policy adoption service protocol.

Computes which policies apply to a solution based on its configuration.
"""

from typing import Protocol, runtime_checkable

from julee.core.entities.policy import Policy, PolicyAdoption, SolutionPolicyConfig


@runtime_checkable
class PolicyAdoptionService(Protocol):
    """Service for computing effective policy adoptions.

    Given a solution's configuration and available policies, determines
    which policies are in effect (adopted, skipped, or not applicable).
    """

    def get_effective_policies(
        self,
        config: SolutionPolicyConfig,
        available_policies: list[Policy],
    ) -> list[PolicyAdoption]:
        """Compute effective policy adoptions for a solution.

        Args:
            config: The solution's policy configuration
            available_policies: All available policies

        Returns:
            List of PolicyAdoption records for all applicable policies
        """
        ...

    def get_policies_to_verify(
        self,
        config: SolutionPolicyConfig,
        available_policies: list[Policy],
    ) -> tuple[list[Policy], list[Policy]]:
        """Get policies that should be verified vs skipped.

        Args:
            config: The solution's policy configuration
            available_policies: All available policies

        Returns:
            Tuple of (policies_to_verify, skipped_policies)
        """
        ...
