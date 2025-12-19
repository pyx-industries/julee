"""CreateAppUseCase.

Use case for creating a new app.
"""

from .....hcd_api.requests import CreateAppRequest
from .....hcd_api.responses import CreateAppResponse
from ...repositories.app import AppRepository


class CreateAppUseCase:
    """Use case for creating an app."""

    def __init__(self, app_repo: AppRepository) -> None:
        """Initialize with repository dependency.

        Args:
            app_repo: App repository instance
        """
        self.app_repo = app_repo

    async def execute(self, request: CreateAppRequest) -> CreateAppResponse:
        """Create a new app.

        Args:
            request: App creation request with app data

        Returns:
            Response containing the created app
        """
        app = request.to_domain_model()
        await self.app_repo.save(app)
        return CreateAppResponse(app=app)
