"""Tests for App CRUD use cases."""

import pytest

from julee.hcd.domain.models.app import App, AppType
from julee.hcd.domain.use_cases.app import (
    CreateAppUseCase,
    DeleteAppUseCase,
    GetAppUseCase,
    ListAppsUseCase,
    UpdateAppUseCase,
)
from julee.hcd.domain.use_cases.requests import (
    CreateAppRequest,
    DeleteAppRequest,
    GetAppRequest,
    ListAppsRequest,
    UpdateAppRequest,
)
from julee.hcd.repositories.memory.app import MemoryAppRepository


class TestCreateAppUseCase:
    """Test creating apps."""

    @pytest.fixture
    def repo(self) -> MemoryAppRepository:
        """Create a fresh repository."""
        return MemoryAppRepository()

    @pytest.fixture
    def use_case(self, repo: MemoryAppRepository) -> CreateAppUseCase:
        """Create the use case with repository."""
        return CreateAppUseCase(repo)

    @pytest.mark.asyncio
    async def test_create_app_success(
        self,
        use_case: CreateAppUseCase,
        repo: MemoryAppRepository,
    ) -> None:
        """Test successfully creating an app."""
        request = CreateAppRequest(
            slug="hr-portal",
            name="HR Self-Service Portal",
            app_type="staff",
            status="active",
            description="Portal for HR self-service tasks",
            accelerators=["auth-service", "notification-hub"],
        )

        response = await use_case.execute(request)

        assert response.app is not None
        assert response.app.slug == "hr-portal"
        assert response.app.name == "HR Self-Service Portal"
        assert response.app.app_type == AppType.STAFF
        assert response.app.status == "active"
        assert len(response.app.accelerators) == 2

        # Verify it's persisted
        stored = await repo.get("hr-portal")
        assert stored is not None

    @pytest.mark.asyncio
    async def test_create_app_with_defaults(self, use_case: CreateAppUseCase) -> None:
        """Test creating app with default values."""
        request = CreateAppRequest(
            slug="minimal-app",
            name="Minimal App",
        )

        response = await use_case.execute(request)

        assert response.app.app_type == AppType.UNKNOWN
        assert response.app.status is None
        assert response.app.description == ""
        assert response.app.accelerators == []

    @pytest.mark.asyncio
    async def test_create_external_app(self, use_case: CreateAppUseCase) -> None:
        """Test creating an external app."""
        request = CreateAppRequest(
            slug="customer-portal",
            name="Customer Portal",
            app_type="external",
        )

        response = await use_case.execute(request)

        assert response.app.app_type == AppType.EXTERNAL


class TestGetAppUseCase:
    """Test getting apps."""

    @pytest.fixture
    def repo(self) -> MemoryAppRepository:
        """Create a fresh repository."""
        return MemoryAppRepository()

    @pytest.fixture
    async def populated_repo(self, repo: MemoryAppRepository) -> MemoryAppRepository:
        """Create repository with sample data."""
        await repo.save(
            App(
                slug="test-app",
                name="Test Application",
                app_type=AppType.STAFF,
                description="A test application",
            )
        )
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryAppRepository) -> GetAppUseCase:
        """Create the use case with populated repository."""
        return GetAppUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_get_existing_app(self, use_case: GetAppUseCase) -> None:
        """Test getting an existing app."""
        request = GetAppRequest(slug="test-app")

        response = await use_case.execute(request)

        assert response.app is not None
        assert response.app.slug == "test-app"
        assert response.app.name == "Test Application"

    @pytest.mark.asyncio
    async def test_get_nonexistent_app(self, use_case: GetAppUseCase) -> None:
        """Test getting a nonexistent app returns None."""
        request = GetAppRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.app is None


class TestListAppsUseCase:
    """Test listing apps."""

    @pytest.fixture
    def repo(self) -> MemoryAppRepository:
        """Create a fresh repository."""
        return MemoryAppRepository()

    @pytest.fixture
    async def populated_repo(self, repo: MemoryAppRepository) -> MemoryAppRepository:
        """Create repository with sample data."""
        apps = [
            App(slug="app-1", name="App One", app_type=AppType.STAFF),
            App(slug="app-2", name="App Two", app_type=AppType.EXTERNAL),
            App(slug="app-3", name="App Three", app_type=AppType.MEMBER_TOOL),
        ]
        for app in apps:
            await repo.save(app)
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryAppRepository) -> ListAppsUseCase:
        """Create the use case with populated repository."""
        return ListAppsUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_list_all_apps(self, use_case: ListAppsUseCase) -> None:
        """Test listing all apps."""
        request = ListAppsRequest()

        response = await use_case.execute(request)

        assert len(response.apps) == 3
        slugs = {a.slug for a in response.apps}
        assert slugs == {"app-1", "app-2", "app-3"}

    @pytest.mark.asyncio
    async def test_list_empty_repo(self, repo: MemoryAppRepository) -> None:
        """Test listing returns empty list when no apps."""
        use_case = ListAppsUseCase(repo)
        request = ListAppsRequest()

        response = await use_case.execute(request)

        assert response.apps == []


class TestUpdateAppUseCase:
    """Test updating apps."""

    @pytest.fixture
    def repo(self) -> MemoryAppRepository:
        """Create a fresh repository."""
        return MemoryAppRepository()

    @pytest.fixture
    async def populated_repo(self, repo: MemoryAppRepository) -> MemoryAppRepository:
        """Create repository with sample data."""
        await repo.save(
            App(
                slug="update-app",
                name="Original Name",
                app_type=AppType.UNKNOWN,
                description="Original description",
                accelerators=["original-accelerator"],
            )
        )
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryAppRepository) -> UpdateAppUseCase:
        """Create the use case with populated repository."""
        return UpdateAppUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_update_name(self, use_case: UpdateAppUseCase) -> None:
        """Test updating the name."""
        request = UpdateAppRequest(
            slug="update-app",
            name="Updated Name",
        )

        response = await use_case.execute(request)

        assert response.app is not None
        assert response.found is True
        assert response.app.name == "Updated Name"
        # Other fields unchanged
        assert response.app.description == "Original description"

    @pytest.mark.asyncio
    async def test_update_app_type(self, use_case: UpdateAppUseCase) -> None:
        """Test updating the app type."""
        request = UpdateAppRequest(
            slug="update-app",
            app_type="staff",
        )

        response = await use_case.execute(request)

        assert response.app.app_type == AppType.STAFF

    @pytest.mark.asyncio
    async def test_update_accelerators(self, use_case: UpdateAppUseCase) -> None:
        """Test updating accelerators list."""
        request = UpdateAppRequest(
            slug="update-app",
            accelerators=["new-accel-1", "new-accel-2"],
        )

        response = await use_case.execute(request)

        assert response.app.accelerators == ["new-accel-1", "new-accel-2"]

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, use_case: UpdateAppUseCase) -> None:
        """Test updating multiple fields."""
        request = UpdateAppRequest(
            slug="update-app",
            name="New Name",
            app_type="external",
            status="deprecated",
            description="New description",
        )

        response = await use_case.execute(request)

        assert response.app.name == "New Name"
        assert response.app.app_type == AppType.EXTERNAL
        assert response.app.status == "deprecated"
        assert response.app.description == "New description"

    @pytest.mark.asyncio
    async def test_update_nonexistent_app(self, use_case: UpdateAppUseCase) -> None:
        """Test updating nonexistent app returns None."""
        request = UpdateAppRequest(
            slug="nonexistent",
            name="New Name",
        )

        response = await use_case.execute(request)

        assert response.app is None
        assert response.found is False


class TestDeleteAppUseCase:
    """Test deleting apps."""

    @pytest.fixture
    def repo(self) -> MemoryAppRepository:
        """Create a fresh repository."""
        return MemoryAppRepository()

    @pytest.fixture
    async def populated_repo(self, repo: MemoryAppRepository) -> MemoryAppRepository:
        """Create repository with sample data."""
        await repo.save(App(slug="to-delete", name="To Delete"))
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryAppRepository) -> DeleteAppUseCase:
        """Create the use case with populated repository."""
        return DeleteAppUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_delete_existing_app(
        self,
        use_case: DeleteAppUseCase,
        populated_repo: MemoryAppRepository,
    ) -> None:
        """Test successfully deleting an app."""
        request = DeleteAppRequest(slug="to-delete")

        response = await use_case.execute(request)

        assert response.deleted is True

        # Verify it's removed
        stored = await populated_repo.get("to-delete")
        assert stored is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_app(self, use_case: DeleteAppUseCase) -> None:
        """Test deleting nonexistent app returns False."""
        request = DeleteAppRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.deleted is False
