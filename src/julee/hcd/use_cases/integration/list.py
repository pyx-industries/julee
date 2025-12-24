"""List integrations use case with co-located request/response."""

from pydantic import BaseModel

from julee.hcd.entities.integration import Integration
from julee.hcd.repositories.integration import IntegrationRepository


class ListIntegrationsRequest(BaseModel):
    """Request for listing integrations."""

    pass


class ListIntegrationsResponse(BaseModel):
    """Response from listing integrations."""

    integrations: list[Integration]


class ListIntegrationsUseCase:
    """Use case for listing all integrations.

    .. usecase-documentation:: julee.hcd.domain.use_cases.integration.list:ListIntegrationsUseCase
    """

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
