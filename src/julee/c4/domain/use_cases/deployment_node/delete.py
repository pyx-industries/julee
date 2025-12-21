"""DeleteDeploymentNodeUseCase.

Use case for deleting a deployment node.
"""

from ..requests import DeleteDeploymentNodeRequest
from ..responses import DeleteDeploymentNodeResponse
from ...repositories.deployment_node import DeploymentNodeRepository


class DeleteDeploymentNodeUseCase:
    """Use case for deleting a deployment node."""

    def __init__(self, deployment_node_repo: DeploymentNodeRepository) -> None:
        """Initialize with repository dependency.

        Args:
            deployment_node_repo: DeploymentNode repository instance
        """
        self.deployment_node_repo = deployment_node_repo

    async def execute(
        self, request: DeleteDeploymentNodeRequest
    ) -> DeleteDeploymentNodeResponse:
        """Delete a deployment node by slug.

        Args:
            request: Delete request containing the deployment node slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.deployment_node_repo.delete(request.slug)
        return DeleteDeploymentNodeResponse(deleted=deleted)
