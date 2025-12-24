"""Tests for MemoryDeploymentNodeRepository."""

import pytest

from julee.c4.entities.deployment_node import (
    ContainerInstance,
    DeploymentNode,
    NodeType,
)
from julee.c4.infrastructure.repositories.memory.deployment_node import (
    MemoryDeploymentNodeRepository,
)


def create_node(
    slug: str = "test-node",
    name: str = "Test Node",
    environment: str = "production",
    node_type: NodeType = NodeType.OTHER,
    parent_slug: str | None = None,
    container_instances: list[ContainerInstance] | None = None,
    docname: str = "",
) -> DeploymentNode:
    """Helper to create test deployment nodes."""
    return DeploymentNode(
        slug=slug,
        name=name,
        environment=environment,
        node_type=node_type,
        parent_slug=parent_slug,
        container_instances=container_instances or [],
        docname=docname,
    )


class TestMemoryDeploymentNodeRepositoryBasicOperations:
    """Test basic CRUD operations."""

    @pytest.fixture
    def repo(self) -> MemoryDeploymentNodeRepository:
        """Create a fresh repository."""
        return MemoryDeploymentNodeRepository()

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo: MemoryDeploymentNodeRepository) -> None:
        """Test saving and retrieving a deployment node."""
        node = create_node(slug="web-server", name="Web Server")
        await repo.save(node)

        retrieved = await repo.get("web-server")
        assert retrieved is not None
        assert retrieved.slug == "web-server"
        assert retrieved.name == "Web Server"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, repo: MemoryDeploymentNodeRepository) -> None:
        """Test getting a nonexistent node returns None."""
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo: MemoryDeploymentNodeRepository) -> None:
        """Test listing all nodes."""
        await repo.save(create_node(slug="node-1"))
        await repo.save(create_node(slug="node-2"))
        await repo.save(create_node(slug="node-3"))

        all_nodes = await repo.list_all()
        assert len(all_nodes) == 3

    @pytest.mark.asyncio
    async def test_delete(self, repo: MemoryDeploymentNodeRepository) -> None:
        """Test deleting a node."""
        await repo.save(create_node(slug="to-delete"))
        assert await repo.get("to-delete") is not None

        result = await repo.delete("to-delete")
        assert result is True
        assert await repo.get("to-delete") is None

    @pytest.mark.asyncio
    async def test_clear(self, repo: MemoryDeploymentNodeRepository) -> None:
        """Test clearing all nodes."""
        await repo.save(create_node(slug="node-1"))
        await repo.save(create_node(slug="node-2"))
        assert len(await repo.list_all()) == 2

        await repo.clear()
        assert len(await repo.list_all()) == 0


class TestMemoryDeploymentNodeRepositoryQueries:
    """Test deployment node-specific query methods."""

    @pytest.fixture
    def repo(self) -> MemoryDeploymentNodeRepository:
        """Create a repository."""
        return MemoryDeploymentNodeRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryDeploymentNodeRepository
    ) -> MemoryDeploymentNodeRepository:
        """Create a repository with sample data."""
        nodes = [
            # Root level - cloud region
            create_node(
                slug="aws-eu",
                name="AWS EU Region",
                environment="production",
                node_type=NodeType.CLOUD_REGION,
                docname="nodes/aws",
            ),
            # Child - availability zone
            create_node(
                slug="eu-west-1a",
                name="EU West 1A",
                environment="production",
                node_type=NodeType.AVAILABILITY_ZONE,
                parent_slug="aws-eu",
                docname="nodes/aws",
            ),
            # Child - kubernetes cluster with containers
            create_node(
                slug="k8s-prod",
                name="Production Kubernetes",
                environment="production",
                node_type=NodeType.KUBERNETES_CLUSTER,
                parent_slug="eu-west-1a",
                container_instances=[
                    ContainerInstance(container_slug="api-app", instance_count=3),
                    ContainerInstance(container_slug="web-app", instance_count=2),
                ],
                docname="nodes/k8s",
            ),
            # Staging environment
            create_node(
                slug="staging-server",
                name="Staging Server",
                environment="staging",
                node_type=NodeType.VIRTUAL_MACHINE,
                container_instances=[
                    ContainerInstance(container_slug="api-app", instance_count=1),
                ],
                docname="nodes/staging",
            ),
        ]
        for node in nodes:
            await repo.save(node)
        return repo

    @pytest.mark.asyncio
    async def test_get_by_environment(
        self, populated_repo: MemoryDeploymentNodeRepository
    ) -> None:
        """Test getting nodes by environment."""
        prod_nodes = await populated_repo.get_by_environment("production")
        assert len(prod_nodes) == 3
        assert all(n.environment == "production" for n in prod_nodes)

    @pytest.mark.asyncio
    async def test_get_by_type(
        self, populated_repo: MemoryDeploymentNodeRepository
    ) -> None:
        """Test getting nodes by type."""
        k8s_nodes = await populated_repo.get_by_type(NodeType.KUBERNETES_CLUSTER)
        assert len(k8s_nodes) == 1
        assert k8s_nodes[0].slug == "k8s-prod"

    @pytest.mark.asyncio
    async def test_get_root_nodes(
        self, populated_repo: MemoryDeploymentNodeRepository
    ) -> None:
        """Test getting root nodes (no parent)."""
        root_nodes = await populated_repo.get_root_nodes()
        assert len(root_nodes) == 2  # aws-eu and staging-server

    @pytest.mark.asyncio
    async def test_get_root_nodes_by_environment(
        self, populated_repo: MemoryDeploymentNodeRepository
    ) -> None:
        """Test getting root nodes filtered by environment."""
        prod_roots = await populated_repo.get_root_nodes(environment="production")
        assert len(prod_roots) == 1
        assert prod_roots[0].slug == "aws-eu"

    @pytest.mark.asyncio
    async def test_get_children(
        self, populated_repo: MemoryDeploymentNodeRepository
    ) -> None:
        """Test getting child nodes."""
        children = await populated_repo.get_children("aws-eu")
        assert len(children) == 1
        assert children[0].slug == "eu-west-1a"

    @pytest.mark.asyncio
    async def test_get_nodes_with_container(
        self, populated_repo: MemoryDeploymentNodeRepository
    ) -> None:
        """Test getting nodes that deploy a specific container."""
        nodes_with_api = await populated_repo.get_nodes_with_container("api-app")
        assert len(nodes_with_api) == 2  # k8s-prod and staging-server

    @pytest.mark.asyncio
    async def test_get_by_docname(
        self, populated_repo: MemoryDeploymentNodeRepository
    ) -> None:
        """Test getting nodes by docname."""
        nodes = await populated_repo.get_by_docname("nodes/aws")
        assert len(nodes) == 2

    @pytest.mark.asyncio
    async def test_clear_by_docname(
        self, populated_repo: MemoryDeploymentNodeRepository
    ) -> None:
        """Test clearing nodes by docname."""
        count = await populated_repo.clear_by_docname("nodes/aws")
        assert count == 2

        remaining = await populated_repo.list_all()
        assert len(remaining) == 2
