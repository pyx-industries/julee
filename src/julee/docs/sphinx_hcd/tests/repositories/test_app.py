"""Tests for MemoryAppRepository."""

import pytest
import pytest_asyncio

from julee.docs.sphinx_hcd.domain.models.app import App, AppType
from julee.docs.sphinx_hcd.repositories.memory.app import MemoryAppRepository


def create_app(
    slug: str = "test-app",
    name: str = "Test App",
    app_type: AppType = AppType.STAFF,
    status: str | None = None,
    accelerators: list[str] | None = None,
) -> App:
    """Helper to create test apps."""
    return App(
        slug=slug,
        name=name,
        app_type=app_type,
        status=status,
        accelerators=accelerators or [],
        manifest_path=f"apps/{slug}/app.yaml",
    )


class TestMemoryAppRepositoryBasicOperations:
    """Test basic CRUD operations."""

    @pytest.fixture
    def repo(self) -> MemoryAppRepository:
        """Create a fresh repository."""
        return MemoryAppRepository()

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo: MemoryAppRepository) -> None:
        """Test saving and retrieving an app."""
        app = create_app(slug="staff-portal")
        await repo.save(app)

        retrieved = await repo.get("staff-portal")
        assert retrieved is not None
        assert retrieved.slug == "staff-portal"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, repo: MemoryAppRepository) -> None:
        """Test getting a nonexistent app returns None."""
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo: MemoryAppRepository) -> None:
        """Test listing all apps."""
        await repo.save(create_app(slug="app-1"))
        await repo.save(create_app(slug="app-2"))
        await repo.save(create_app(slug="app-3"))

        all_apps = await repo.list_all()
        assert len(all_apps) == 3
        slugs = {a.slug for a in all_apps}
        assert slugs == {"app-1", "app-2", "app-3"}

    @pytest.mark.asyncio
    async def test_delete(self, repo: MemoryAppRepository) -> None:
        """Test deleting an app."""
        await repo.save(create_app(slug="to-delete"))
        assert await repo.get("to-delete") is not None

        result = await repo.delete("to-delete")
        assert result is True
        assert await repo.get("to-delete") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, repo: MemoryAppRepository) -> None:
        """Test deleting a nonexistent app."""
        result = await repo.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear(self, repo: MemoryAppRepository) -> None:
        """Test clearing all apps."""
        await repo.save(create_app(slug="app-1"))
        await repo.save(create_app(slug="app-2"))
        assert len(await repo.list_all()) == 2

        await repo.clear()
        assert len(await repo.list_all()) == 0


class TestMemoryAppRepositoryQueries:
    """Test app-specific query methods."""

    @pytest.fixture
    def repo(self) -> MemoryAppRepository:
        """Create a repository with sample data."""
        return MemoryAppRepository()

    @pytest_asyncio.fixture
    async def populated_repo(self, repo: MemoryAppRepository) -> MemoryAppRepository:
        """Create a repository with sample apps."""
        apps = [
            create_app(
                slug="staff-portal",
                name="Staff Portal",
                app_type=AppType.STAFF,
                accelerators=["user-auth", "doc-upload"],
            ),
            create_app(
                slug="admin-tool",
                name="Admin Tool",
                app_type=AppType.STAFF,
                accelerators=["admin-config"],
            ),
            create_app(
                slug="customer-portal",
                name="Customer Portal",
                app_type=AppType.EXTERNAL,
            ),
            create_app(
                slug="checkout-app",
                name="Checkout App",
                app_type=AppType.EXTERNAL,
                accelerators=["payment-processor"],
            ),
            create_app(
                slug="member-tool",
                name="Member Tool",
                app_type=AppType.MEMBER_TOOL,
            ),
        ]
        for app in apps:
            await repo.save(app)
        return repo

    @pytest.mark.asyncio
    async def test_get_by_type_staff(
        self, populated_repo: MemoryAppRepository
    ) -> None:
        """Test getting apps by staff type."""
        apps = await populated_repo.get_by_type(AppType.STAFF)
        assert len(apps) == 2
        assert all(a.app_type == AppType.STAFF for a in apps)

    @pytest.mark.asyncio
    async def test_get_by_type_external(
        self, populated_repo: MemoryAppRepository
    ) -> None:
        """Test getting apps by external type."""
        apps = await populated_repo.get_by_type(AppType.EXTERNAL)
        assert len(apps) == 2
        assert all(a.app_type == AppType.EXTERNAL for a in apps)

    @pytest.mark.asyncio
    async def test_get_by_type_member_tool(
        self, populated_repo: MemoryAppRepository
    ) -> None:
        """Test getting apps by member-tool type."""
        apps = await populated_repo.get_by_type(AppType.MEMBER_TOOL)
        assert len(apps) == 1
        assert apps[0].slug == "member-tool"

    @pytest.mark.asyncio
    async def test_get_by_type_no_results(
        self, populated_repo: MemoryAppRepository
    ) -> None:
        """Test getting apps by type with no matches."""
        apps = await populated_repo.get_by_type(AppType.UNKNOWN)
        assert len(apps) == 0

    @pytest.mark.asyncio
    async def test_get_by_name(self, populated_repo: MemoryAppRepository) -> None:
        """Test getting an app by name."""
        app = await populated_repo.get_by_name("Staff Portal")
        assert app is not None
        assert app.slug == "staff-portal"

    @pytest.mark.asyncio
    async def test_get_by_name_case_insensitive(
        self, populated_repo: MemoryAppRepository
    ) -> None:
        """Test name matching is case-insensitive."""
        app = await populated_repo.get_by_name("staff portal")
        assert app is not None
        assert app.slug == "staff-portal"

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(
        self, populated_repo: MemoryAppRepository
    ) -> None:
        """Test getting app by nonexistent name."""
        app = await populated_repo.get_by_name("Nonexistent App")
        assert app is None

    @pytest.mark.asyncio
    async def test_get_all_types(self, populated_repo: MemoryAppRepository) -> None:
        """Test getting all unique app types."""
        types = await populated_repo.get_all_types()
        assert types == {AppType.STAFF, AppType.EXTERNAL, AppType.MEMBER_TOOL}

    @pytest.mark.asyncio
    async def test_get_apps_with_accelerators(
        self, populated_repo: MemoryAppRepository
    ) -> None:
        """Test getting apps that have accelerators."""
        apps = await populated_repo.get_apps_with_accelerators()
        assert len(apps) == 3
        slugs = {a.slug for a in apps}
        assert slugs == {"staff-portal", "admin-tool", "checkout-app"}

    @pytest.mark.asyncio
    async def test_get_apps_with_accelerators_empty(
        self, repo: MemoryAppRepository
    ) -> None:
        """Test getting apps with accelerators when none have any."""
        await repo.save(create_app(slug="no-accel-1"))
        await repo.save(create_app(slug="no-accel-2"))

        apps = await repo.get_apps_with_accelerators()
        assert len(apps) == 0
