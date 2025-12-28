"""ListApplicationsUseCase with co-located request/response.

Use case for listing all applications discovered in a codebase.
"""

from pydantic import BaseModel

from julee.core.decorators import use_case
from julee.core.entities.application import Application
from julee.core.repositories.application import ApplicationRepository


class ListApplicationsRequest(BaseModel):
    """Request for listing applications.

    Extensible for future filtering options.
    """

    pass


class ListApplicationsResponse(BaseModel):
    """Response from listing applications."""

    applications: list[Application]


@use_case
class ListApplicationsUseCase:
    """Use case for listing all applications.

    Returns all applications discovered in the solution's apps/ directory.
    """

    def __init__(self, application_repo: ApplicationRepository) -> None:
        """Initialize with repository dependency.

        Args:
            application_repo: Repository for discovering applications
        """
        self.application_repo = application_repo

    async def execute(
        self, request: ListApplicationsRequest
    ) -> ListApplicationsResponse:
        """List all applications.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all discovered applications
        """
        applications = await self.application_repo.list_all()
        return ListApplicationsResponse(applications=applications)
