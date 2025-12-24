"""Delete deployment node use case with co-located request/response."""

from pydantic import BaseModel

from ...repositories.deployment_node import DeploymentNodeRepository


class DeleteDeploymentNodeRequest(BaseModel):
    """Request for deleting a deployment node by slug."""

    slug: str


class DeleteDeploymentNodeResponse(BaseModel):
    """Response from deleting a deployment node."""

    deleted: bool


class DeleteDeploymentNodeUseCase:
    """Use case for deleting a deployment node.

    .. usecase-documentation:: julee.c4.domain.use_cases.deployment_node.delete:DeleteDeploymentNodeUseCase
    """

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
