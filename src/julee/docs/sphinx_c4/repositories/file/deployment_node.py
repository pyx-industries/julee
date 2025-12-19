"""File-backed DeploymentNode repository implementation."""

import json
import logging
from pathlib import Path

from ...domain.models.deployment_node import DeploymentNode, NodeType
from ...domain.repositories.deployment_node import DeploymentNodeRepository
from .base import FileRepositoryMixin

logger = logging.getLogger(__name__)


class FileDeploymentNodeRepository(
    FileRepositoryMixin[DeploymentNode], DeploymentNodeRepository
):
    """File-backed implementation of DeploymentNodeRepository.

    Stores deployment nodes as JSON files in the specified directory.
    File structure: {base_path}/{slug}.json
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize repository with base path.

        Args:
            base_path: Directory to store deployment node JSON files
        """
        self.base_path = base_path
        self.storage: dict[str, DeploymentNode] = {}
        self.entity_name = "DeploymentNode"
        self.id_field = "slug"
        self._load_all()

    def _get_file_path(self, entity: DeploymentNode) -> Path:
        """Get file path for a deployment node."""
        return self.base_path / f"{entity.slug}.json"

    def _serialize(self, entity: DeploymentNode) -> str:
        """Serialize deployment node to JSON."""
        return entity.model_dump_json(indent=2)

    def _load_all(self) -> None:
        """Load all deployment nodes from disk."""
        if not self.base_path.exists():
            logger.debug(f"FileDeploymentNodeRepository: Base path does not exist: {self.base_path}")
            return

        for file_path in self.base_path.glob("*.json"):
            try:
                content = file_path.read_text(encoding="utf-8")
                data = json.loads(content)
                node = DeploymentNode.model_validate(data)
                self.storage[node.slug] = node
                logger.debug(f"FileDeploymentNodeRepository: Loaded {node.slug}")
            except Exception as e:
                logger.warning(f"FileDeploymentNodeRepository: Failed to load {file_path}: {e}")

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
        return [
            n for n in self.storage.values() if n.deploys_container(container_slug)
        ]

    async def get_by_docname(self, docname: str) -> list[DeploymentNode]:
        """Get nodes defined in a specific document."""
        return [n for n in self.storage.values() if n.docname == docname]

    async def clear_by_docname(self, docname: str) -> int:
        """Clear nodes defined in a specific document."""
        to_remove = [
            slug for slug, n in self.storage.items() if n.docname == docname
        ]
        for slug in to_remove:
            await self.delete(slug)
        return len(to_remove)
