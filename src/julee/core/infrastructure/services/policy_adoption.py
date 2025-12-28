"""Policy adoption service implementation.

Computes which policies apply to a solution based on its configuration.
"""

from julee.core.entities.policy import Policy, PolicyAdoption, SolutionPolicyConfig


class DefaultPolicyAdoptionService:
    """Default implementation of policy adoption computation.

    Applies the following rules:
    1. Non-julee solutions get no policies
    2. Julee solutions get framework-default policies (unless skipped)
    3. Explicitly adopted policies are added
    """

    def get_effective_policies(
        self,
        config: SolutionPolicyConfig,
        available_policies: list[Policy],
    ) -> list[PolicyAdoption]:
        """Compute effective policy adoptions for a solution."""
        adoptions: list[PolicyAdoption] = []

        if not config.is_julee_solution:
            return adoptions

        # Framework defaults (unless skipped)
        for policy in available_policies:
            if policy.framework_default:
                skipped = policy.slug in config.skip_policies
                adoptions.append(
                    PolicyAdoption(
                        policy_slug=policy.slug,
                        source="framework_default",
                        skipped=skipped,
                    )
                )

        # Explicit adoptions
        policy_map = {p.slug: p for p in available_policies}
        for slug in config.policies:
            if slug in policy_map:
                existing = next((a for a in adoptions if a.policy_slug == slug), None)
                if existing is None:
                    adoptions.append(
                        PolicyAdoption(
                            policy_slug=slug,
                            source="explicit",
                            skipped=False,
                        )
                    )

        return adoptions

    def get_policies_to_verify(
        self,
        config: SolutionPolicyConfig,
        available_policies: list[Policy],
    ) -> tuple[list[Policy], list[Policy]]:
        """Get policies that should be verified vs skipped."""
        adoptions = self.get_effective_policies(config, available_policies)
        policy_map = {p.slug: p for p in available_policies}

        to_verify: list[Policy] = []
        skipped: list[Policy] = []

        for adoption in adoptions:
            policy = policy_map.get(adoption.policy_slug)
            if policy:
                if adoption.skipped:
                    skipped.append(policy)
                else:
                    to_verify.append(policy)

        return to_verify, skipped
