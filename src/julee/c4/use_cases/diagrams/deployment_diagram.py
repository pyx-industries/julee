"""GetDeploymentDiagramUseCase with co-located request/response.

Use case for computing a deployment diagram.

A Deployment diagram shows how containers are deployed to infrastructure
nodes in a specific environment.
"""

from pydantic import BaseModel, Field

from julee.c4.entities.container import Container
from julee.c4.entities.diagrams import DeploymentDiagram
from julee.c4.repositories.container import ContainerRepository
from julee.c4.repositories.deployment_node import DeploymentNodeRepository
from julee.c4.repositories.relationship import RelationshipRepository
from julee.core.decorators import use_case


class GetDeploymentDiagramRequest(BaseModel):
    """Request for generating a deployment diagram."""

    environment: str = Field(description="Deployment environment to show")
    format: str = Field(
        default="plantuml", description="Output format: plantuml, structurizr, data"
    )


class GetDeploymentDiagramResponse(BaseModel):
    """Response from computing a deployment diagram."""

    diagram: DeploymentDiagram


@use_case
class GetDeploymentDiagramUseCase:
    """Use case for computing a deployment diagram.

    .. usecase-documentation:: julee.c4.domain.use_cases.diagrams.deployment_diagram:GetDeploymentDiagramUseCase

    The diagram shows:
    - Infrastructure nodes in the environment
    - Container instances deployed to nodes
    - Relationships between deployed containers
    """

    def __init__(
        self,
        deployment_node_repo: DeploymentNodeRepository,
        container_repo: ContainerRepository,
        relationship_repo: RelationshipRepository,
    ) -> None:
        """Initialize with repository dependencies.

        Args:
            deployment_node_repo: DeploymentNode repository instance
            container_repo: Container repository instance
            relationship_repo: Relationship repository instance
        """
        self.deployment_node_repo = deployment_node_repo
        self.container_repo = container_repo
        self.relationship_repo = relationship_repo

    async def execute(
        self, request: GetDeploymentDiagramRequest
    ) -> GetDeploymentDiagramResponse:
        """Compute the deployment diagram data.

        Args:
            request: Request containing environment name

        Returns:
            Response containing diagram with nodes, containers, and relationships
        """
        nodes = await self.deployment_node_repo.get_by_environment(request.environment)

        container_slugs: set[str] = set()
        for node in nodes:
            for instance in node.container_instances:
                container_slugs.add(instance.container_slug)

        containers: list[Container] = []
        for slug in container_slugs:
            container = await self.container_repo.get(slug)
            if container:
                containers.append(container)

        relationships = await self.relationship_repo.get_between_containers("")

        relevant_relationships = [
            rel
            for rel in relationships
            if rel.source_slug in container_slugs
            or rel.destination_slug in container_slugs
        ]

        diagram = DeploymentDiagram(
            environment=request.environment,
            nodes=nodes,
            containers=containers,
            relationships=relevant_relationships,
        )
        return GetDeploymentDiagramResponse(diagram=diagram)
