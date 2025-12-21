"""CreateDeploymentNodeUseCase.

Use case for creating a new deployment node.
"""

from ...repositories.deployment_node import DeploymentNodeRepository
from ..requests import CreateDeploymentNodeRequest
from ..responses import CreateDeploymentNodeResponse


class CreateDeploymentNodeUseCase:
    """Use case for creating a deployment node."""

    def __init__(self, deployment_node_repo: DeploymentNodeRepository) -> None:
        """Initialize with repository dependency.

        Args:
            deployment_node_repo: DeploymentNode repository instance
        """
        self.deployment_node_repo = deployment_node_repo

    async def execute(
        self, request: CreateDeploymentNodeRequest
    ) -> CreateDeploymentNodeResponse:
        """Create a new deployment node.

        Args:
            request: Deployment node creation request with data

        Returns:
            Response containing the created deployment node
        """
        deployment_node = request.to_domain_model()
        await self.deployment_node_repo.save(deployment_node)
        return CreateDeploymentNodeResponse(deployment_node=deployment_node)
