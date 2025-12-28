"""SphinxEnv implementation of DeploymentNodeRepository."""

from julee.c4.entities.deployment_node import DeploymentNode, NodeType
from julee.c4.repositories.deployment_node import DeploymentNodeRepository

from .base import SphinxEnvC4RepositoryMixin


class SphinxEnvDeploymentNodeRepository(
    SphinxEnvC4RepositoryMixin[DeploymentNode], DeploymentNodeRepository
):
    """SphinxEnv implementation of DeploymentNodeRepository."""

    entity_class = DeploymentNode

    async def get_by_environment(self, environment: str) -> list[DeploymentNode]:
        """Get all nodes in a specific environment."""
        return await self.find_by_field("environment", environment)

    async def get_by_type(self, node_type: NodeType) -> list[DeploymentNode]:
        """Get nodes of a specific type."""
        all_nodes = await self.list_all()
        return [n for n in all_nodes if n.node_type == node_type]

    async def get_root_nodes(
        self, environment: str | None = None
    ) -> list[DeploymentNode]:
        """Get top-level nodes (no parent)."""
        all_nodes = await self.list_all()
        roots = [n for n in all_nodes if not n.parent_slug]
        if environment:
            roots = [n for n in roots if n.environment == environment]
        return roots

    async def get_children(self, parent_slug: str) -> list[DeploymentNode]:
        """Get child nodes of a parent node."""
        return await self.find_by_field("parent_slug", parent_slug)

    async def get_nodes_with_container(
        self, container_slug: str
    ) -> list[DeploymentNode]:
        """Get nodes that deploy a specific container."""
        all_nodes = await self.list_all()
        return [
            n for n in all_nodes
            if container_slug in (n.container_instances or [])
        ]
