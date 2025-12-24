"""CreateIntegrationUseCase.

Use case for creating a new integration.
"""

from ...repositories.integration import IntegrationRepository
from ..requests import CreateIntegrationRequest
from ..responses import CreateIntegrationResponse


class CreateIntegrationUseCase:
    """Use case for creating an integration.

    .. usecase-documentation:: julee.hcd.domain.use_cases.integration.create:CreateIntegrationUseCase
    """

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
