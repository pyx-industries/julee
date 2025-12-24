"""Tests for Component CRUD use cases."""

import pytest

from julee.c4.domain.models.component import Component
from julee.c4.domain.use_cases.component import (
    CreateComponentRequest,
    CreateComponentUseCase,
    DeleteComponentRequest,
    DeleteComponentUseCase,
    GetComponentRequest,
    GetComponentUseCase,
    ListComponentsRequest,
    ListComponentsUseCase,
    UpdateComponentRequest,
    UpdateComponentUseCase,
)
from julee.c4.repositories.memory.component import (
    MemoryComponentRepository,
)


class TestCreateComponentUseCase:
    """Test creating components."""

    @pytest.fixture
    def repo(self) -> MemoryComponentRepository:
        """Create a fresh repository."""
        return MemoryComponentRepository()

    @pytest.fixture
    def use_case(self, repo: MemoryComponentRepository) -> CreateComponentUseCase:
        """Create the use case with repository."""
        return CreateComponentUseCase(repo)

    @pytest.mark.asyncio
    async def test_create_component_success(
        self,
        use_case: CreateComponentUseCase,
        repo: MemoryComponentRepository,
    ) -> None:
        """Test successfully creating a component."""
        request = CreateComponentRequest(
            slug="auth-controller",
            name="Auth Controller",
            container_slug="api-app",
            system_slug="banking-system",
            description="Handles authentication",
            technology="Python class",
            interface="REST endpoints",
            tags=["auth", "security"],
        )

        response = await use_case.execute(request)

        assert response.component is not None
        assert response.component.slug == "auth-controller"
        assert response.component.name == "Auth Controller"
        assert response.component.container_slug == "api-app"
        assert response.component.system_slug == "banking-system"

        # Verify it's persisted
        stored = await repo.get("auth-controller")
        assert stored is not None
        assert stored.name == "Auth Controller"

    @pytest.mark.asyncio
    async def test_create_component_with_defaults(
        self, use_case: CreateComponentUseCase
    ) -> None:
        """Test creating with minimal required fields uses defaults."""
        request = CreateComponentRequest(
            slug="simple-component",
            name="Simple Component",
            container_slug="container",
            system_slug="system",
        )

        response = await use_case.execute(request)

        assert response.component.description == ""
        assert response.component.technology == ""
        assert response.component.interface == ""
        assert response.component.tags == []


class TestGetComponentUseCase:
    """Test getting components."""

    @pytest.fixture
    def repo(self) -> MemoryComponentRepository:
        """Create a fresh repository."""
        return MemoryComponentRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryComponentRepository
    ) -> MemoryComponentRepository:
        """Create repository with sample data."""
        await repo.save(
            Component(
                slug="auth-controller",
                name="Auth Controller",
                container_slug="api-app",
                system_slug="banking-system",
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryComponentRepository
    ) -> GetComponentUseCase:
        """Create the use case with populated repository."""
        return GetComponentUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_get_existing_component(self, use_case: GetComponentUseCase) -> None:
        """Test getting an existing component."""
        request = GetComponentRequest(slug="auth-controller")

        response = await use_case.execute(request)

        assert response.component is not None
        assert response.component.slug == "auth-controller"
        assert response.component.name == "Auth Controller"

    @pytest.mark.asyncio
    async def test_get_nonexistent_component(
        self, use_case: GetComponentUseCase
    ) -> None:
        """Test getting a nonexistent component returns None."""
        request = GetComponentRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.component is None


class TestListComponentsUseCase:
    """Test listing components."""

    @pytest.fixture
    def repo(self) -> MemoryComponentRepository:
        """Create a fresh repository."""
        return MemoryComponentRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryComponentRepository
    ) -> MemoryComponentRepository:
        """Create repository with sample data."""
        components = [
            Component(
                slug="comp-1",
                name="Component 1",
                container_slug="container",
                system_slug="system",
            ),
            Component(
                slug="comp-2",
                name="Component 2",
                container_slug="container",
                system_slug="system",
            ),
            Component(
                slug="comp-3",
                name="Component 3",
                container_slug="container",
                system_slug="system",
            ),
        ]
        for c in components:
            await repo.save(c)
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryComponentRepository
    ) -> ListComponentsUseCase:
        """Create the use case with populated repository."""
        return ListComponentsUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_list_all_components(self, use_case: ListComponentsUseCase) -> None:
        """Test listing all components."""
        request = ListComponentsRequest()

        response = await use_case.execute(request)

        assert len(response.components) == 3
        slugs = {c.slug for c in response.components}
        assert slugs == {"comp-1", "comp-2", "comp-3"}

    @pytest.mark.asyncio
    async def test_list_empty_repo(self, repo: MemoryComponentRepository) -> None:
        """Test listing returns empty list when no components."""
        use_case = ListComponentsUseCase(repo)
        request = ListComponentsRequest()

        response = await use_case.execute(request)

        assert response.components == []


class TestUpdateComponentUseCase:
    """Test updating components."""

    @pytest.fixture
    def repo(self) -> MemoryComponentRepository:
        """Create a fresh repository."""
        return MemoryComponentRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryComponentRepository
    ) -> MemoryComponentRepository:
        """Create repository with sample data."""
        await repo.save(
            Component(
                slug="auth-controller",
                name="Auth Controller",
                container_slug="api-app",
                system_slug="banking-system",
                description="Original description",
                technology="Python",
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryComponentRepository
    ) -> UpdateComponentUseCase:
        """Create the use case with populated repository."""
        return UpdateComponentUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_update_single_field(
        self,
        use_case: UpdateComponentUseCase,
        populated_repo: MemoryComponentRepository,
    ) -> None:
        """Test updating a single field."""
        request = UpdateComponentRequest(
            slug="auth-controller",
            name="Updated Auth Controller",
        )

        response = await use_case.execute(request)

        assert response.component is not None
        assert response.component.name == "Updated Auth Controller"
        # Other fields unchanged
        assert response.component.description == "Original description"
        assert response.component.technology == "Python"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(
        self, use_case: UpdateComponentUseCase
    ) -> None:
        """Test updating multiple fields."""
        request = UpdateComponentRequest(
            slug="auth-controller",
            description="New description",
            technology="FastAPI controller",
            interface="REST API",
        )

        response = await use_case.execute(request)

        assert response.component.description == "New description"
        assert response.component.technology == "FastAPI controller"
        assert response.component.interface == "REST API"

    @pytest.mark.asyncio
    async def test_update_nonexistent_component(
        self, use_case: UpdateComponentUseCase
    ) -> None:
        """Test updating nonexistent component returns None."""
        request = UpdateComponentRequest(
            slug="nonexistent",
            name="New Name",
        )

        response = await use_case.execute(request)

        assert response.component is None


class TestDeleteComponentUseCase:
    """Test deleting components."""

    @pytest.fixture
    def repo(self) -> MemoryComponentRepository:
        """Create a fresh repository."""
        return MemoryComponentRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryComponentRepository
    ) -> MemoryComponentRepository:
        """Create repository with sample data."""
        await repo.save(
            Component(
                slug="to-delete",
                name="To Delete",
                container_slug="container",
                system_slug="system",
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryComponentRepository
    ) -> DeleteComponentUseCase:
        """Create the use case with populated repository."""
        return DeleteComponentUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_delete_existing_component(
        self,
        use_case: DeleteComponentUseCase,
        populated_repo: MemoryComponentRepository,
    ) -> None:
        """Test successfully deleting a component."""
        request = DeleteComponentRequest(slug="to-delete")

        response = await use_case.execute(request)

        assert response.deleted is True

        # Verify it's removed
        stored = await populated_repo.get("to-delete")
        assert stored is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_component(
        self, use_case: DeleteComponentUseCase
    ) -> None:
        """Test deleting nonexistent component returns False."""
        request = DeleteComponentRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.deleted is False
