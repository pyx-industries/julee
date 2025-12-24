"""In-memory DeploymentNode repository implementation."""

from ...domain.models.deployment_node import DeploymentNode, NodeType
from ...domain.repositories.deployment_node import DeploymentNodeRepository
from .base import MemoryRepositoryMixin


class MemoryDeploymentNodeRepository(
    MemoryRepositoryMixin[DeploymentNode], DeploymentNodeRepository
):
    """In-memory implementation of DeploymentNodeRepository.

    Stores deployment nodes in a dictionary keyed by slug.
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        self.storage: dict[str, DeploymentNode] = {}
        self.entity_name = "DeploymentNode"
        self.id_field = "slug"

    async def get_by_environment(self, environment: str) -> list[DeploymentNode]:
        """Get all nodes in a specific environment."""
        return [n for n in self.storage.values() if n.environment == environment]

    async def get_by_type(self, node_type: NodeType) -> list[DeploymentNode]:
        """Get nodes of a specific type."""
        return [n for n in self.storage.values() if n.node_type == node_type]

    async def get_root_nodes(
        self, environment: str | None = None
    ) -> list[DeploymentNode]:
        """Get top-level nodes (no parent)."""
        nodes = [n for n in self.storage.values() if not n.has_parent]
        if environment:
            nodes = [n for n in nodes if n.environment == environment]
        return nodes

    async def get_children(self, parent_slug: str) -> list[DeploymentNode]:
        """Get child nodes of a parent node."""
        return [n for n in self.storage.values() if n.parent_slug == parent_slug]

    async def get_nodes_with_container(
        self, container_slug: str
    ) -> list[DeploymentNode]:
        """Get nodes that deploy a specific container."""
        return [n for n in self.storage.values() if n.deploys_container(container_slug)]

    async def get_by_docname(self, docname: str) -> list[DeploymentNode]:
        """Get nodes defined in a specific document."""
        return [n for n in self.storage.values() if n.docname == docname]

    async def clear_by_docname(self, docname: str) -> int:
        """Clear nodes defined in a specific document."""
        to_remove = [slug for slug, n in self.storage.items() if n.docname == docname]
        for slug in to_remove:
            del self.storage[slug]
        return len(to_remove)
