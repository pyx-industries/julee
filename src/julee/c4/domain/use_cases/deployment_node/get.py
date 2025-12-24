"""Get deployment node use case with co-located request/response."""

from pydantic import BaseModel

from ...models.deployment_node import DeploymentNode
from ...repositories.deployment_node import DeploymentNodeRepository


class GetDeploymentNodeRequest(BaseModel):
    """Request for getting a deployment node by slug."""

    slug: str


class GetDeploymentNodeResponse(BaseModel):
    """Response from getting a deployment node."""

    deployment_node: DeploymentNode | None


class GetDeploymentNodeUseCase:
    """Use case for getting a deployment node by slug.

    .. usecase-documentation:: julee.c4.domain.use_cases.deployment_node.get:GetDeploymentNodeUseCase
    """

    def __init__(self, deployment_node_repo: DeploymentNodeRepository) -> None:
        """Initialize with repository dependency.

        Args:
            deployment_node_repo: DeploymentNode repository instance
        """
        self.deployment_node_repo = deployment_node_repo

    async def execute(
        self, request: GetDeploymentNodeRequest
    ) -> GetDeploymentNodeResponse:
        """Get a deployment node by slug.

        Args:
            request: Request containing the deployment node slug

        Returns:
            Response containing the deployment node if found, or None
        """
        deployment_node = await self.deployment_node_repo.get(request.slug)
        return GetDeploymentNodeResponse(deployment_node=deployment_node)
