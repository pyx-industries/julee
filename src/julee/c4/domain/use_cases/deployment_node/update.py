"""UpdateDeploymentNodeUseCase.

Use case for updating an existing deployment node.
"""

from ..requests import UpdateDeploymentNodeRequest
from ..responses import UpdateDeploymentNodeResponse
from ...repositories.deployment_node import DeploymentNodeRepository


class UpdateDeploymentNodeUseCase:
    """Use case for updating a deployment node."""

    def __init__(self, deployment_node_repo: DeploymentNodeRepository) -> None:
        """Initialize with repository dependency.

        Args:
            deployment_node_repo: DeploymentNode repository instance
        """
        self.deployment_node_repo = deployment_node_repo

    async def execute(
        self, request: UpdateDeploymentNodeRequest
    ) -> UpdateDeploymentNodeResponse:
        """Update an existing deployment node.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated deployment node if found
        """
        existing = await self.deployment_node_repo.get(request.slug)
        if not existing:
            return UpdateDeploymentNodeResponse(deployment_node=None, found=False)

        updated = request.apply_to(existing)
        await self.deployment_node_repo.save(updated)
        return UpdateDeploymentNodeResponse(deployment_node=updated, found=True)
