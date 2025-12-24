"""Update app use case with co-located request/response."""

from typing import Any

from pydantic import BaseModel

from julee.hcd.entities.app import App, AppType

from ...repositories.app import AppRepository


class UpdateAppRequest(BaseModel):
    """Request for updating an app."""

    slug: str
    name: str | None = None
    app_type: str | None = None
    status: str | None = None
    description: str | None = None
    accelerators: list[str] | None = None

    def apply_to(self, existing: App) -> App:
        """Apply non-None fields to existing app."""
        updates: dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name
        if self.app_type is not None:
            updates["app_type"] = AppType.from_string(self.app_type)
        if self.status is not None:
            updates["status"] = self.status
        if self.description is not None:
            updates["description"] = self.description
        if self.accelerators is not None:
            updates["accelerators"] = self.accelerators
        return existing.model_copy(update=updates) if updates else existing


class UpdateAppResponse(BaseModel):
    """Response from updating an app."""

    app: App | None
    found: bool = True


class UpdateAppUseCase:
    """Use case for updating an app.

    .. usecase-documentation:: julee.hcd.domain.use_cases.app.update:UpdateAppUseCase
    """

    def __init__(self, app_repo: AppRepository) -> None:
        """Initialize with repository dependency.

        Args:
            app_repo: App repository instance
        """
        self.app_repo = app_repo

    async def execute(self, request: UpdateAppRequest) -> UpdateAppResponse:
        """Update an existing app.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated app if found
        """
        existing = await self.app_repo.get(request.slug)
        if not existing:
            return UpdateAppResponse(app=None, found=False)

        updated = request.apply_to(existing)
        await self.app_repo.save(updated)
        return UpdateAppResponse(app=updated, found=True)
