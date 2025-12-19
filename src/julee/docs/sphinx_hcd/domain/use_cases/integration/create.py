"""CreateIntegrationUseCase.

Use case for creating a new integration.
"""

from .....hcd_api.requests import CreateIntegrationRequest
from .....hcd_api.responses import CreateIntegrationResponse
from ...repositories.integration import IntegrationRepository


class CreateIntegrationUseCase:
    """Use case for creating an integration."""

    def __init__(self, integration_repo: IntegrationRepository) -> None:
        """Initialize with repository dependency.

        Args:
            integration_repo: Integration repository instance
        """
        self.integration_repo = integration_repo

    async def execute(
        self, request: CreateIntegrationRequest
    ) -> CreateIntegrationResponse:
        """Create a new integration.

        Args:
            request: Integration creation request with integration data

        Returns:
            Response containing the created integration
        """
        integration = request.to_domain_model()
        await self.integration_repo.save(integration)
        return CreateIntegrationResponse(integration=integration)
