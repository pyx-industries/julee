"""Policy repository protocol.

Defines the interface for accessing available policies.
"""

from typing import Protocol, runtime_checkable

from julee.core.entities.policy import Policy


@runtime_checkable
class PolicyRepository(Protocol):
    """Repository for accessing available policies.

    Provides read-only access to the registered policies.
    The primary implementation reads from the policy registry.
    """

    async def list_policies(self) -> list[Policy]:
        """List all available policies.

        Returns:
            All registered policies
        """
        ...

    async def get_policy(self, slug: str) -> Policy | None:
        """Get a policy by slug.

        Args:
            slug: The policy identifier

        Returns:
            Policy if found, None otherwise
        """
        ...

    async def get_framework_defaults(self) -> list[Policy]:
        """Get policies that apply by default to julee solutions.

        Returns:
            Policies with framework_default=True
        """
        ...
