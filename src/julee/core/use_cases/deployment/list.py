"""ListDeploymentsUseCase with co-located request/response.

Use case for listing all deployments discovered in a codebase.
"""

from pydantic import BaseModel

from julee.core.decorators import use_case
from julee.core.entities.deployment import Deployment
from julee.core.repositories.deployment import DeploymentRepository


class ListDeploymentsRequest(BaseModel):
    """Request for listing deployments.

    Extensible for future filtering options.
    """

    pass


class ListDeploymentsResponse(BaseModel):
    """Response from listing deployments."""

    deployments: list[Deployment]


@use_case
class ListDeploymentsUseCase:
    """Use case for listing all deployments.

    Returns all deployments discovered in the solution's deployments/ directory.
    """

    def __init__(self, deployment_repo: DeploymentRepository) -> None:
        """Initialize with repository dependency.

        Args:
            deployment_repo: Repository for discovering deployments
        """
        self.deployment_repo = deployment_repo

    async def execute(self, request: ListDeploymentsRequest) -> ListDeploymentsResponse:
        """List all deployments.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all discovered deployments
        """
        deployments = await self.deployment_repo.list_all()
        return ListDeploymentsResponse(deployments=deployments)
