"""GetDeploymentNodeUseCase.

Use case for getting a deployment node by slug.
"""

from .....c4_api.requests import GetDeploymentNodeRequest
from .....c4_api.responses import GetDeploymentNodeResponse
from ...repositories.deployment_node import DeploymentNodeRepository


class GetDeploymentNodeUseCase:
    """Use case for getting a deployment node by slug."""

    def __init__(self, deployment_node_repo: DeploymentNodeRepository) -> None:
        """Initialize with repository dependency.

        Args:
            deployment_node_repo: DeploymentNode repository instance
        """
        self.deployment_node_repo = deployment_node_repo

    async def execute(self, request: GetDeploymentNodeRequest) -> GetDeploymentNodeResponse:
        """Get a deployment node by slug.

        Args:
            request: Request containing the deployment node slug

        Returns:
            Response containing the deployment node if found, or None
        """
        deployment_node = await self.deployment_node_repo.get(request.slug)
        return GetDeploymentNodeResponse(deployment_node=deployment_node)
