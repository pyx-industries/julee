"""DeploymentNodeRepository protocol."""

from typing import Protocol, runtime_checkable

from ..models.deployment_node import DeploymentNode, NodeType
from .base import BaseRepository


@runtime_checkable
class DeploymentNodeRepository(BaseRepository[DeploymentNode], Protocol):
    """Repository protocol for DeploymentNode entities.

    Extends BaseRepository with deployment-specific queries needed
    for C4 deployment diagram generation.
    """

    async def get_by_environment(self, environment: str) -> list[DeploymentNode]:
        """Get all nodes in a specific environment.

        Args:
            environment: Environment name (e.g., "production", "staging")

        Returns:
            List of nodes in that environment
        """
        ...

    async def get_by_type(self, node_type: NodeType) -> list[DeploymentNode]:
        """Get nodes of a specific type.

        Args:
            node_type: physical_server, kubernetes_cluster, etc.

        Returns:
            List of nodes matching the type
        """
        ...

    async def get_root_nodes(self, environment: str | None = None) -> list[DeploymentNode]:
        """Get top-level nodes (no parent).

        Args:
            environment: Optional filter by environment

        Returns:
            List of root deployment nodes
        """
        ...

    async def get_children(self, parent_slug: str) -> list[DeploymentNode]:
        """Get child nodes of a parent node.

        Args:
            parent_slug: Parent node's slug

        Returns:
            List of child nodes
        """
        ...

    async def get_nodes_with_container(
        self, container_slug: str
    ) -> list[DeploymentNode]:
        """Get nodes that deploy a specific container.

        Args:
            container_slug: Container to find

        Returns:
            List of nodes deploying that container
        """
        ...

    async def get_by_docname(self, docname: str) -> list[DeploymentNode]:
        """Get nodes defined in a specific document.

        Args:
            docname: Sphinx document name

        Returns:
            List of nodes defined in that document
        """
        ...

    async def clear_by_docname(self, docname: str) -> int:
        """Clear nodes defined in a specific document.

        Args:
            docname: Sphinx document name

        Returns:
            Number of nodes removed
        """
        ...
