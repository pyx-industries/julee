"""Tests for Container CRUD use cases."""

import pytest

from julee.c4.domain.models.container import (
    Container,
    ContainerType,
)
from julee.c4.domain.use_cases.container import (
    CreateContainerUseCase,
    DeleteContainerUseCase,
    GetContainerUseCase,
    ListContainersUseCase,
    UpdateContainerUseCase,
)
from julee.c4.domain.use_cases.requests import (
    CreateContainerRequest,
    DeleteContainerRequest,
    GetContainerRequest,
    ListContainersRequest,
    UpdateContainerRequest,
)
from julee.c4.repositories.memory.container import (
    MemoryContainerRepository,
)


class TestCreateContainerUseCase:
    """Test creating containers."""

    @pytest.fixture
    def repo(self) -> MemoryContainerRepository:
        """Create a fresh repository."""
        return MemoryContainerRepository()

    @pytest.fixture
    def use_case(self, repo: MemoryContainerRepository) -> CreateContainerUseCase:
        """Create the use case with repository."""
        return CreateContainerUseCase(repo)

    @pytest.mark.asyncio
    async def test_create_container_success(
        self,
        use_case: CreateContainerUseCase,
        repo: MemoryContainerRepository,
    ) -> None:
        """Test successfully creating a container."""
        request = CreateContainerRequest(
            slug="api-app",
            name="API Application",
            system_slug="banking-system",
            description="REST API backend",
            container_type="api",
            technology="FastAPI, Python 3.11",
            tags=["backend", "core"],
        )

        response = await use_case.execute(request)

        assert response.container is not None
        assert response.container.slug == "api-app"
        assert response.container.name == "API Application"
        assert response.container.system_slug == "banking-system"
        assert response.container.container_type == ContainerType.API

        # Verify it's persisted
        stored = await repo.get("api-app")
        assert stored is not None
        assert stored.name == "API Application"

    @pytest.mark.asyncio
    async def test_create_container_with_defaults(
        self, use_case: CreateContainerUseCase
    ) -> None:
        """Test creating with minimal required fields uses defaults."""
        request = CreateContainerRequest(
            slug="simple-app",
            name="Simple App",
            system_slug="test-system",
        )

        response = await use_case.execute(request)

        assert response.container.description == ""
        assert response.container.container_type == ContainerType.OTHER
        assert response.container.tags == []


class TestGetContainerUseCase:
    """Test getting containers."""

    @pytest.fixture
    def repo(self) -> MemoryContainerRepository:
        """Create a fresh repository."""
        return MemoryContainerRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryContainerRepository
    ) -> MemoryContainerRepository:
        """Create repository with sample data."""
        await repo.save(
            Container(
                slug="api-app",
                name="API Application",
                system_slug="banking-system",
                container_type=ContainerType.API,
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryContainerRepository
    ) -> GetContainerUseCase:
        """Create the use case with populated repository."""
        return GetContainerUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_get_existing_container(self, use_case: GetContainerUseCase) -> None:
        """Test getting an existing container."""
        request = GetContainerRequest(slug="api-app")

        response = await use_case.execute(request)

        assert response.container is not None
        assert response.container.slug == "api-app"
        assert response.container.name == "API Application"

    @pytest.mark.asyncio
    async def test_get_nonexistent_container(
        self, use_case: GetContainerUseCase
    ) -> None:
        """Test getting a nonexistent container returns None."""
        request = GetContainerRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.container is None


class TestListContainersUseCase:
    """Test listing containers."""

    @pytest.fixture
    def repo(self) -> MemoryContainerRepository:
        """Create a fresh repository."""
        return MemoryContainerRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryContainerRepository
    ) -> MemoryContainerRepository:
        """Create repository with sample data."""
        containers = [
            Container(slug="container-1", name="Container 1", system_slug="sys"),
            Container(slug="container-2", name="Container 2", system_slug="sys"),
            Container(slug="container-3", name="Container 3", system_slug="sys"),
        ]
        for c in containers:
            await repo.save(c)
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryContainerRepository
    ) -> ListContainersUseCase:
        """Create the use case with populated repository."""
        return ListContainersUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_list_all_containers(self, use_case: ListContainersUseCase) -> None:
        """Test listing all containers."""
        request = ListContainersRequest()

        response = await use_case.execute(request)

        assert len(response.containers) == 3
        slugs = {c.slug for c in response.containers}
        assert slugs == {"container-1", "container-2", "container-3"}

    @pytest.mark.asyncio
    async def test_list_empty_repo(self, repo: MemoryContainerRepository) -> None:
        """Test listing returns empty list when no containers."""
        use_case = ListContainersUseCase(repo)
        request = ListContainersRequest()

        response = await use_case.execute(request)

        assert response.containers == []


class TestUpdateContainerUseCase:
    """Test updating containers."""

    @pytest.fixture
    def repo(self) -> MemoryContainerRepository:
        """Create a fresh repository."""
        return MemoryContainerRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryContainerRepository
    ) -> MemoryContainerRepository:
        """Create repository with sample data."""
        await repo.save(
            Container(
                slug="api-app",
                name="API Application",
                system_slug="banking-system",
                description="Original description",
                container_type=ContainerType.API,
                technology="Python",
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryContainerRepository
    ) -> UpdateContainerUseCase:
        """Create the use case with populated repository."""
        return UpdateContainerUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_update_single_field(
        self,
        use_case: UpdateContainerUseCase,
        populated_repo: MemoryContainerRepository,
    ) -> None:
        """Test updating a single field."""
        request = UpdateContainerRequest(
            slug="api-app",
            name="Updated API Application",
        )

        response = await use_case.execute(request)

        assert response.container is not None
        assert response.container.name == "Updated API Application"
        # Other fields unchanged
        assert response.container.description == "Original description"
        assert response.container.technology == "Python"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(
        self, use_case: UpdateContainerUseCase
    ) -> None:
        """Test updating multiple fields."""
        request = UpdateContainerRequest(
            slug="api-app",
            description="New description",
            technology="FastAPI, Python 3.11",
            container_type="web_application",
        )

        response = await use_case.execute(request)

        assert response.container.description == "New description"
        assert response.container.technology == "FastAPI, Python 3.11"
        assert response.container.container_type == ContainerType.WEB_APPLICATION

    @pytest.mark.asyncio
    async def test_update_nonexistent_container(
        self, use_case: UpdateContainerUseCase
    ) -> None:
        """Test updating nonexistent container returns None."""
        request = UpdateContainerRequest(
            slug="nonexistent",
            name="New Name",
        )

        response = await use_case.execute(request)

        assert response.container is None


class TestDeleteContainerUseCase:
    """Test deleting containers."""

    @pytest.fixture
    def repo(self) -> MemoryContainerRepository:
        """Create a fresh repository."""
        return MemoryContainerRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryContainerRepository
    ) -> MemoryContainerRepository:
        """Create repository with sample data."""
        await repo.save(
            Container(slug="to-delete", name="To Delete", system_slug="sys")
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryContainerRepository
    ) -> DeleteContainerUseCase:
        """Create the use case with populated repository."""
        return DeleteContainerUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_delete_existing_container(
        self,
        use_case: DeleteContainerUseCase,
        populated_repo: MemoryContainerRepository,
    ) -> None:
        """Test successfully deleting a container."""
        request = DeleteContainerRequest(slug="to-delete")

        response = await use_case.execute(request)

        assert response.deleted is True

        # Verify it's removed
        stored = await populated_repo.get("to-delete")
        assert stored is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_container(
        self, use_case: DeleteContainerUseCase
    ) -> None:
        """Test deleting nonexistent container returns False."""
        request = DeleteContainerRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.deleted is False
