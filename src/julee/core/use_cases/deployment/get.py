"""GetDeploymentUseCase with co-located request/response.

Use case for getting a single deployment by slug.
"""

from pydantic import BaseModel

from julee.core.decorators import use_case
from julee.core.entities.deployment import Deployment
from julee.core.repositories.deployment import DeploymentRepository


class GetDeploymentRequest(BaseModel):
    """Request for getting a deployment."""

    slug: str


class GetDeploymentResponse(BaseModel):
    """Response from getting a deployment."""

    deployment: Deployment | None = None


@use_case
class GetDeploymentUseCase:
    """Use case for getting a single deployment by slug."""

    def __init__(self, deployment_repo: DeploymentRepository) -> None:
        """Initialize with repository dependency.

        Args:
            deployment_repo: Repository for discovering deployments
        """
        self.deployment_repo = deployment_repo

    async def execute(self, request: GetDeploymentRequest) -> GetDeploymentResponse:
        """Get a deployment by slug.

        Args:
            request: Get request with slug

        Returns:
            Response containing the deployment if found
        """
        deployment = await self.deployment_repo.get(request.slug)
        return GetDeploymentResponse(deployment=deployment)
