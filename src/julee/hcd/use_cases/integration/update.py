"""Update integration use case with co-located request/response."""

from typing import Any

from pydantic import BaseModel

from julee.hcd.entities.integration import Direction, Integration
from julee.hcd.repositories.integration import IntegrationRepository

from .create import ExternalDependencyItem


class UpdateIntegrationRequest(BaseModel):
    """Request for updating an integration."""

    slug: str
    name: str | None = None
    description: str | None = None
    direction: str | None = None
    depends_on: list[ExternalDependencyItem] | None = None

    def apply_to(self, existing: Integration) -> Integration:
        """Apply non-None fields to existing integration."""
        updates: dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name
        if self.description is not None:
            updates["description"] = self.description
        if self.direction is not None:
            updates["direction"] = Direction.from_string(self.direction)
        if self.depends_on is not None:
            updates["depends_on"] = [d.to_domain_model() for d in self.depends_on]
        return existing.model_copy(update=updates) if updates else existing


class UpdateIntegrationResponse(BaseModel):
    """Response from updating an integration."""

    integration: Integration | None
    found: bool = True


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
