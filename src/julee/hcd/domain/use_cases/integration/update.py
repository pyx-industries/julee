"""UpdateIntegrationUseCase.

Use case for updating an existing integration.
"""

from ...repositories.integration import IntegrationRepository
from ..requests import UpdateIntegrationRequest
from ..responses import UpdateIntegrationResponse


class UpdateIntegrationUseCase:
    """Use case for updating an integration.

    .. usecase-documentation:: julee.hcd.domain.use_cases.integration.update:UpdateIntegrationUseCase
    """

    def __init__(self, integration_repo: IntegrationRepository) -> None:
        """Initialize with repository dependency.

        Args:
            integration_repo: Integration repository instance
        """
        self.integration_repo = integration_repo

    async def execute(
        self, request: UpdateIntegrationRequest
    ) -> UpdateIntegrationResponse:
        """Update an existing integration.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated integration if found
        """
        existing = await self.integration_repo.get(request.slug)
        if not existing:
            return UpdateIntegrationResponse(integration=None, found=False)

        updated = request.apply_to(existing)
        await self.integration_repo.save(updated)
        return UpdateIntegrationResponse(integration=updated, found=True)
