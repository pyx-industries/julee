"""GetApplicationUseCase with co-located request/response.

Use case for getting a single application by slug.
"""

from pydantic import BaseModel

from julee.core.decorators import use_case
from julee.core.entities.application import Application
from julee.core.repositories.application import ApplicationRepository


class GetApplicationRequest(BaseModel):
    """Request for getting an application."""

    slug: str


class GetApplicationResponse(BaseModel):
    """Response from getting an application."""

    application: Application | None = None


@use_case
class GetApplicationUseCase:
    """Use case for getting a single application by slug."""

    def __init__(self, application_repo: ApplicationRepository) -> None:
        """Initialize with repository dependency.

        Args:
            application_repo: Repository for discovering applications
        """
        self.application_repo = application_repo

    async def execute(self, request: GetApplicationRequest) -> GetApplicationResponse:
        """Get an application by slug.

        Args:
            request: Get request with slug

        Returns:
            Response containing the application if found
        """
        application = await self.application_repo.get(request.slug)
        return GetApplicationResponse(application=application)
