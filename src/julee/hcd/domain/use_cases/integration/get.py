"""Get integration use case with co-located request/response."""

from pydantic import BaseModel

from ...models.integration import Integration
from ...repositories.integration import IntegrationRepository


class GetIntegrationRequest(BaseModel):
    """Request for getting an integration by slug."""

    slug: str


class GetIntegrationResponse(BaseModel):
    """Response from getting an integration."""

    integration: Integration | None


class GetIntegrationUseCase:
    """Use case for getting an integration by slug.

    .. usecase-documentation:: julee.hcd.domain.use_cases.integration.get:GetIntegrationUseCase
    """

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
