"""Update deployment node use case with co-located request/response."""

from typing import Any

from pydantic import BaseModel, Field

from ...models.deployment_node import DeploymentNode, NodeType
from ...repositories.deployment_node import DeploymentNodeRepository
from .create import ContainerInstanceItem


class UpdateDeploymentNodeRequest(BaseModel):
    """Request for updating a deployment node."""

    slug: str
    name: str | None = None
    environment: str | None = None
    node_type: str | None = None
    technology: str | None = None
    description: str | None = None
    parent_slug: str | None = Field(default=None)
    container_instances: list[ContainerInstanceItem] | None = None
    properties: dict[str, str] | None = None
    tags: list[str] | None = None

    def apply_to(self, existing: DeploymentNode) -> DeploymentNode:
        """Apply non-None fields to existing deployment node."""
        updates: dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name
        if self.environment is not None:
            updates["environment"] = self.environment
        if self.node_type is not None:
            updates["node_type"] = NodeType(self.node_type)
        if self.technology is not None:
            updates["technology"] = self.technology
        if self.description is not None:
            updates["description"] = self.description
        if self.parent_slug is not None:
            updates["parent_slug"] = self.parent_slug
        if self.container_instances is not None:
            updates["container_instances"] = [
                ci.to_domain_model() for ci in self.container_instances
            ]
        if self.properties is not None:
            updates["properties"] = self.properties
        if self.tags is not None:
            updates["tags"] = self.tags
        return existing.model_copy(update=updates) if updates else existing


class UpdateDeploymentNodeResponse(BaseModel):
    """Response from updating a deployment node."""

    deployment_node: DeploymentNode | None
    found: bool = True


class UpdateDeploymentNodeUseCase:
    """Use case for updating a deployment node.

    .. usecase-documentation:: julee.c4.domain.use_cases.deployment_node.update:UpdateDeploymentNodeUseCase
    """

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
