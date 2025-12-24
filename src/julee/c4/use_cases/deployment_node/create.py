"""Create deployment node use case with co-located request/response."""

from pydantic import BaseModel, Field, field_validator

from julee.c4.entities.deployment_node import (
    ContainerInstance,
    DeploymentNode,
    NodeType,
)
from julee.c4.repositories.deployment_node import DeploymentNodeRepository


class ContainerInstanceItem(BaseModel):
    """Nested item representing a container instance."""

    container_slug: str = Field(description="Slug of deployed container")
    instance_id: str = Field(default="", description="Instance identifier")
    properties: dict[str, str] = Field(
        default_factory=dict, description="Instance properties"
    )

    def to_domain_model(self) -> ContainerInstance:
        """Convert to ContainerInstance."""
        return ContainerInstance(
            container_slug=self.container_slug,
            instance_id=self.instance_id,
            properties=self.properties,
        )


class CreateDeploymentNodeRequest(BaseModel):
    """Request model for creating a deployment node."""

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    environment: str = Field(default="production", description="Deployment environment")
    node_type: str = Field(default="other", description="Type of infrastructure node")
    technology: str = Field(default="", description="Infrastructure technology")
    description: str = Field(default="", description="Human-readable description")
    parent_slug: str | None = Field(default=None, description="Parent node for nesting")
    container_instances: list[ContainerInstanceItem] = Field(
        default_factory=list, description="Containers deployed to this node"
    )
    properties: dict[str, str] = Field(
        default_factory=dict, description="Node properties"
    )
    tags: list[str] = Field(default_factory=list, description="Classification tags")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    def to_domain_model(self) -> DeploymentNode:
        """Convert to DeploymentNode."""
        return DeploymentNode(
            slug=self.slug,
            name=self.name,
            environment=self.environment,
            node_type=NodeType(self.node_type),
            technology=self.technology,
            description=self.description,
            parent_slug=self.parent_slug,
            container_instances=[
                ci.to_domain_model() for ci in self.container_instances
            ],
            properties=self.properties,
            tags=self.tags,
            docname="",
        )


class CreateDeploymentNodeResponse(BaseModel):
    """Response from creating a deployment node."""

    deployment_node: DeploymentNode


class CreateDeploymentNodeUseCase:
    """Use case for creating a deployment node.

    .. usecase-documentation:: julee.c4.domain.use_cases.deployment_node.create:CreateDeploymentNodeUseCase
    """

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
