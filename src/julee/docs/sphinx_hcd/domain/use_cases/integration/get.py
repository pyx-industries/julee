"""GetIntegrationUseCase.

Use case for getting an integration by slug.
"""

from .....hcd_api.requests import GetIntegrationRequest
from .....hcd_api.responses import GetIntegrationResponse
from ...repositories.integration import IntegrationRepository


class GetIntegrationUseCase:
    """Use case for getting an integration by slug."""

    def __init__(self, integration_repo: IntegrationRepository) -> None:
        """Initialize with repository dependency.

        Args:
            integration_repo: Integration repository instance
        """
        self.integration_repo = integration_repo

    async def execute(self, request: GetIntegrationRequest) -> GetIntegrationResponse:
        """Get an integration by slug.

        Args:
            request: Request containing the integration slug

        Returns:
            Response containing the integration if found, or None
        """
        integration = await self.integration_repo.get(request.slug)
        return GetIntegrationResponse(integration=integration)
