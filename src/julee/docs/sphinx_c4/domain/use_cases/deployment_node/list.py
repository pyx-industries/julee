"""ListDeploymentNodesUseCase.

Use case for listing all deployment nodes.
"""

from .....c4_api.requests import ListDeploymentNodesRequest
from .....c4_api.responses import ListDeploymentNodesResponse
from ...repositories.deployment_node import DeploymentNodeRepository


class ListDeploymentNodesUseCase:
    """Use case for listing all deployment nodes."""

    def __init__(self, deployment_node_repo: DeploymentNodeRepository) -> None:
        """Initialize with repository dependency.

        Args:
            deployment_node_repo: DeploymentNode repository instance
        """
        self.deployment_node_repo = deployment_node_repo

    async def execute(
        self, request: ListDeploymentNodesRequest
    ) -> ListDeploymentNodesResponse:
        """List all deployment nodes.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all deployment nodes
        """
        deployment_nodes = await self.deployment_node_repo.list_all()
        return ListDeploymentNodesResponse(deployment_nodes=deployment_nodes)
