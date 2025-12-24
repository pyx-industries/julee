"""ListDeploymentNodesUseCase.

Use case for listing all deployment nodes.
"""

from ...repositories.deployment_node import DeploymentNodeRepository
from ..requests import ListDeploymentNodesRequest
from ..responses import ListDeploymentNodesResponse


class ListDeploymentNodesUseCase:
    """Use case for listing all deployment nodes.

    .. usecase-documentation:: julee.c4.domain.use_cases.deployment_node.list:ListDeploymentNodesUseCase
    """

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
