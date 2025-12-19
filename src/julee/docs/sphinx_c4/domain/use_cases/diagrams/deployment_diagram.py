"""GetDeploymentDiagramUseCase.

Use case for computing a deployment diagram.

A Deployment diagram shows how containers are deployed to infrastructure
nodes in a specific environment.
"""

from dataclasses import dataclass, field

from ...models.container import Container
from ...models.deployment_node import DeploymentNode
from ...models.relationship import Relationship
from ...repositories.container import ContainerRepository
from ...repositories.deployment_node import DeploymentNodeRepository
from ...repositories.relationship import RelationshipRepository


@dataclass
class DeploymentDiagramData:
    """Data for rendering a deployment diagram."""

    environment: str
    nodes: list[DeploymentNode] = field(default_factory=list)
    containers: list[Container] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)


class GetDeploymentDiagramUseCase:
    """Use case for computing a deployment diagram.

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

    async def execute(self, environment: str) -> DeploymentDiagramData:
        """Compute the deployment diagram data.

        Args:
            environment: Name of the deployment environment to show

        Returns:
            Diagram data containing nodes, containers, and relationships
        """
        nodes = await self.deployment_node_repo.get_by_environment(environment)

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
            rel for rel in relationships
            if rel.source_slug in container_slugs or rel.destination_slug in container_slugs
        ]

        return DeploymentDiagramData(
            environment=environment,
            nodes=nodes,
            containers=containers,
            relationships=relevant_relationships,
        )
