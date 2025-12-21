"""DeleteIntegrationUseCase.

Use case for deleting an integration.
"""

from ..requests import DeleteIntegrationRequest
from ..responses import DeleteIntegrationResponse
from ...repositories.integration import IntegrationRepository


class DeleteIntegrationUseCase:
    """Use case for deleting an integration."""

    def __init__(self, integration_repo: IntegrationRepository) -> None:
        """Initialize with repository dependency.

        Args:
            integration_repo: Integration repository instance
        """
        self.integration_repo = integration_repo

    async def execute(
        self, request: DeleteIntegrationRequest
    ) -> DeleteIntegrationResponse:
        """Delete an integration by slug.

        Args:
            request: Delete request containing the integration slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.integration_repo.delete(request.slug)
        return DeleteIntegrationResponse(deleted=deleted)
