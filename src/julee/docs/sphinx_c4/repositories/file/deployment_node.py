"""File-backed DeploymentNode repository implementation."""

import logging
from pathlib import Path

from ...domain.models.deployment_node import DeploymentNode, NodeType
from ...domain.repositories.deployment_node import DeploymentNodeRepository
from ...parsers.rst import scan_deployment_node_directory
from ...serializers.rst import serialize_deployment_node
from .base import FileRepositoryMixin

logger = logging.getLogger(__name__)


class FileDeploymentNodeRepository(
    FileRepositoryMixin[DeploymentNode], DeploymentNodeRepository
):
    """File-backed implementation of DeploymentNodeRepository.

    Stores deployment nodes as RST files with define-deployment-node directives.
    File structure: {base_path}/{slug}.rst
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize repository with base path.

        Args:
            base_path: Directory to store deployment node RST files
        """
        self.base_path = base_path
        self.storage: dict[str, DeploymentNode] = {}
        self.entity_name = "DeploymentNode"
        self.id_field = "slug"
        self._load_all()

    def _get_file_path(self, entity: DeploymentNode) -> Path:
        """Get file path for a deployment node."""
        return self.base_path / f"{entity.slug}.rst"

    def _serialize(self, entity: DeploymentNode) -> str:
        """Serialize deployment node to RST format."""
        return serialize_deployment_node(entity)

    def _load_all(self) -> None:
        """Load all deployment nodes from disk."""
        if not self.base_path.exists():
            logger.debug(
                f"FileDeploymentNodeRepository: Base path does not exist: {self.base_path}"
            )
            return

        nodes = scan_deployment_node_directory(self.base_path)
        for node in nodes:
            self.storage[node.slug] = node

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
            await self.delete(slug)
        return len(to_remove)
