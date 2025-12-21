"""ListIntegrationsUseCase.

Use case for listing all integrations.
"""

from ..requests import ListIntegrationsRequest
from ..responses import ListIntegrationsResponse
from ...repositories.integration import IntegrationRepository


class ListIntegrationsUseCase:
    """Use case for listing all integrations."""

    def __init__(self, integration_repo: IntegrationRepository) -> None:
        """Initialize with repository dependency.

        Args:
            integration_repo: Integration repository instance
        """
        self.integration_repo = integration_repo

    async def execute(
        self, request: ListIntegrationsRequest
    ) -> ListIntegrationsResponse:
        """List all integrations.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all integrations
        """
        integrations = await self.integration_repo.list_all()
        return ListIntegrationsResponse(integrations=integrations)
