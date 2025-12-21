"""Tests for DeploymentNode CRUD use cases."""

import pytest

from julee.c4.domain.use_cases.requests import (
    CreateDeploymentNodeRequest,
    DeleteDeploymentNodeRequest,
    GetDeploymentNodeRequest,
    ListDeploymentNodesRequest,
    UpdateDeploymentNodeRequest,
)
from julee.c4.domain.models.deployment_node import (
    DeploymentNode,
    NodeType,
)
from julee.c4.domain.use_cases.deployment_node import (
    CreateDeploymentNodeUseCase,
    DeleteDeploymentNodeUseCase,
    GetDeploymentNodeUseCase,
    ListDeploymentNodesUseCase,
    UpdateDeploymentNodeUseCase,
)
from julee.c4.repositories.memory.deployment_node import (
    MemoryDeploymentNodeRepository,
)


class TestCreateDeploymentNodeUseCase:
    """Test creating deployment nodes."""

    @pytest.fixture
    def repo(self) -> MemoryDeploymentNodeRepository:
        """Create a fresh repository."""
        return MemoryDeploymentNodeRepository()

    @pytest.fixture
    def use_case(
        self, repo: MemoryDeploymentNodeRepository
    ) -> CreateDeploymentNodeUseCase:
        """Create the use case with repository."""
        return CreateDeploymentNodeUseCase(repo)

    @pytest.mark.asyncio
    async def test_create_deployment_node_success(
        self,
        use_case: CreateDeploymentNodeUseCase,
        repo: MemoryDeploymentNodeRepository,
    ) -> None:
        """Test successfully creating a deployment node."""
        request = CreateDeploymentNodeRequest(
            slug="aws-region-eu",
            name="AWS EU Region",
            environment="production",
            node_type="cloud_region",
            technology="AWS",
            description="European data center",
            tags=["aws", "eu"],
        )

        response = await use_case.execute(request)

        assert response.deployment_node is not None
        assert response.deployment_node.slug == "aws-region-eu"
        assert response.deployment_node.name == "AWS EU Region"
        assert response.deployment_node.environment == "production"
        assert response.deployment_node.node_type == NodeType.CLOUD_REGION

        # Verify it's persisted
        stored = await repo.get("aws-region-eu")
        assert stored is not None
        assert stored.name == "AWS EU Region"

    @pytest.mark.asyncio
    async def test_create_deployment_node_with_parent(
        self,
        use_case: CreateDeploymentNodeUseCase,
        repo: MemoryDeploymentNodeRepository,
    ) -> None:
        """Test creating deployment node with parent reference."""
        request = CreateDeploymentNodeRequest(
            slug="web-server",
            name="Web Server",
            environment="production",
            node_type="physical_server",
            parent_slug="aws-region",
        )

        response = await use_case.execute(request)

        assert response.deployment_node is not None
        assert response.deployment_node.parent_slug == "aws-region"
        assert response.deployment_node.has_parent is True

    @pytest.mark.asyncio
    async def test_create_deployment_node_with_defaults(
        self, use_case: CreateDeploymentNodeUseCase
    ) -> None:
        """Test creating with minimal required fields uses defaults."""
        request = CreateDeploymentNodeRequest(
            slug="simple-node",
            name="Simple Node",
        )

        response = await use_case.execute(request)

        assert response.deployment_node.environment == "production"
        assert response.deployment_node.node_type == NodeType.OTHER
        assert response.deployment_node.description == ""
        assert response.deployment_node.container_instances == []


class TestGetDeploymentNodeUseCase:
    """Test getting deployment nodes."""

    @pytest.fixture
    def repo(self) -> MemoryDeploymentNodeRepository:
        """Create a fresh repository."""
        return MemoryDeploymentNodeRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryDeploymentNodeRepository
    ) -> MemoryDeploymentNodeRepository:
        """Create repository with sample data."""
        await repo.save(
            DeploymentNode(
                slug="web-server",
                name="Web Server",
                environment="production",
                node_type=NodeType.PHYSICAL_SERVER,
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryDeploymentNodeRepository
    ) -> GetDeploymentNodeUseCase:
        """Create the use case with populated repository."""
        return GetDeploymentNodeUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_get_existing_deployment_node(
        self, use_case: GetDeploymentNodeUseCase
    ) -> None:
        """Test getting an existing deployment node."""
        request = GetDeploymentNodeRequest(slug="web-server")

        response = await use_case.execute(request)

        assert response.deployment_node is not None
        assert response.deployment_node.slug == "web-server"
        assert response.deployment_node.name == "Web Server"

    @pytest.mark.asyncio
    async def test_get_nonexistent_deployment_node(
        self, use_case: GetDeploymentNodeUseCase
    ) -> None:
        """Test getting a nonexistent deployment node returns None."""
        request = GetDeploymentNodeRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.deployment_node is None


class TestListDeploymentNodesUseCase:
    """Test listing deployment nodes."""

    @pytest.fixture
    def repo(self) -> MemoryDeploymentNodeRepository:
        """Create a fresh repository."""
        return MemoryDeploymentNodeRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryDeploymentNodeRepository
    ) -> MemoryDeploymentNodeRepository:
        """Create repository with sample data."""
        nodes = [
            DeploymentNode(slug="node-1", name="Node 1"),
            DeploymentNode(slug="node-2", name="Node 2"),
            DeploymentNode(slug="node-3", name="Node 3"),
        ]
        for n in nodes:
            await repo.save(n)
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryDeploymentNodeRepository
    ) -> ListDeploymentNodesUseCase:
        """Create the use case with populated repository."""
        return ListDeploymentNodesUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_list_all_deployment_nodes(
        self, use_case: ListDeploymentNodesUseCase
    ) -> None:
        """Test listing all deployment nodes."""
        request = ListDeploymentNodesRequest()

        response = await use_case.execute(request)

        assert len(response.deployment_nodes) == 3
        slugs = {n.slug for n in response.deployment_nodes}
        assert slugs == {"node-1", "node-2", "node-3"}

    @pytest.mark.asyncio
    async def test_list_empty_repo(self, repo: MemoryDeploymentNodeRepository) -> None:
        """Test listing returns empty list when no nodes."""
        use_case = ListDeploymentNodesUseCase(repo)
        request = ListDeploymentNodesRequest()

        response = await use_case.execute(request)

        assert response.deployment_nodes == []


class TestUpdateDeploymentNodeUseCase:
    """Test updating deployment nodes."""

    @pytest.fixture
    def repo(self) -> MemoryDeploymentNodeRepository:
        """Create a fresh repository."""
        return MemoryDeploymentNodeRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryDeploymentNodeRepository
    ) -> MemoryDeploymentNodeRepository:
        """Create repository with sample data."""
        await repo.save(
            DeploymentNode(
                slug="web-server",
                name="Web Server",
                environment="production",
                node_type=NodeType.PHYSICAL_SERVER,
                description="Original description",
                technology="Linux",
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryDeploymentNodeRepository
    ) -> UpdateDeploymentNodeUseCase:
        """Create the use case with populated repository."""
        return UpdateDeploymentNodeUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_update_single_field(
        self,
        use_case: UpdateDeploymentNodeUseCase,
        populated_repo: MemoryDeploymentNodeRepository,
    ) -> None:
        """Test updating a single field."""
        request = UpdateDeploymentNodeRequest(
            slug="web-server",
            name="Updated Web Server",
        )

        response = await use_case.execute(request)

        assert response.deployment_node is not None
        assert response.deployment_node.name == "Updated Web Server"
        # Other fields unchanged
        assert response.deployment_node.description == "Original description"
        assert response.deployment_node.technology == "Linux"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(
        self, use_case: UpdateDeploymentNodeUseCase
    ) -> None:
        """Test updating multiple fields."""
        request = UpdateDeploymentNodeRequest(
            slug="web-server",
            description="New description",
            technology="Ubuntu 22.04",
            node_type="container_runtime",
        )

        response = await use_case.execute(request)

        assert response.deployment_node.description == "New description"
        assert response.deployment_node.technology == "Ubuntu 22.04"
        assert response.deployment_node.node_type == NodeType.CONTAINER_RUNTIME

    @pytest.mark.asyncio
    async def test_update_environment(
        self, use_case: UpdateDeploymentNodeUseCase
    ) -> None:
        """Test updating environment."""
        request = UpdateDeploymentNodeRequest(
            slug="web-server",
            environment="staging",
        )

        response = await use_case.execute(request)

        assert response.deployment_node is not None
        assert response.deployment_node.environment == "staging"

    @pytest.mark.asyncio
    async def test_update_nonexistent_deployment_node(
        self, use_case: UpdateDeploymentNodeUseCase
    ) -> None:
        """Test updating nonexistent deployment node returns None."""
        request = UpdateDeploymentNodeRequest(
            slug="nonexistent",
            name="New Name",
        )

        response = await use_case.execute(request)

        assert response.deployment_node is None


class TestDeleteDeploymentNodeUseCase:
    """Test deleting deployment nodes."""

    @pytest.fixture
    def repo(self) -> MemoryDeploymentNodeRepository:
        """Create a fresh repository."""
        return MemoryDeploymentNodeRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryDeploymentNodeRepository
    ) -> MemoryDeploymentNodeRepository:
        """Create repository with sample data."""
        await repo.save(DeploymentNode(slug="to-delete", name="To Delete"))
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryDeploymentNodeRepository
    ) -> DeleteDeploymentNodeUseCase:
        """Create the use case with populated repository."""
        return DeleteDeploymentNodeUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_delete_existing_deployment_node(
        self,
        use_case: DeleteDeploymentNodeUseCase,
        populated_repo: MemoryDeploymentNodeRepository,
    ) -> None:
        """Test successfully deleting a deployment node."""
        request = DeleteDeploymentNodeRequest(slug="to-delete")

        response = await use_case.execute(request)

        assert response.deleted is True

        # Verify it's removed
        stored = await populated_repo.get("to-delete")
        assert stored is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_deployment_node(
        self, use_case: DeleteDeploymentNodeUseCase
    ) -> None:
        """Test deleting nonexistent deployment node returns False."""
        request = DeleteDeploymentNodeRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.deleted is False
