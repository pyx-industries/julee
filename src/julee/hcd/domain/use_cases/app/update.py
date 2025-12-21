"""UpdateAppUseCase.

Use case for updating an existing app.
"""

from ..requests import UpdateAppRequest
from ..responses import UpdateAppResponse
from ...repositories.app import AppRepository


class UpdateAppUseCase:
    """Use case for updating an app."""

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
