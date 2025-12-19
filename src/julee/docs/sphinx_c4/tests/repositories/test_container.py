"""Tests for MemoryContainerRepository."""

import pytest

from julee.docs.sphinx_c4.domain.models.container import Container, ContainerType
from julee.docs.sphinx_c4.repositories.memory.container import (
    MemoryContainerRepository,
)


def create_container(
    slug: str = "test-container",
    name: str = "Test Container",
    system_slug: str = "test-system",
    container_type: ContainerType = ContainerType.OTHER,
    tags: list[str] | None = None,
    docname: str = "",
) -> Container:
    """Helper to create test containers."""
    return Container(
        slug=slug,
        name=name,
        system_slug=system_slug,
        container_type=container_type,
        tags=tags or [],
        docname=docname,
    )


class TestMemoryContainerRepositoryBasicOperations:
    """Test basic CRUD operations."""

    @pytest.fixture
    def repo(self) -> MemoryContainerRepository:
        """Create a fresh repository."""
        return MemoryContainerRepository()

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo: MemoryContainerRepository) -> None:
        """Test saving and retrieving a container."""
        container = create_container(slug="api-app", name="API Application")
        await repo.save(container)

        retrieved = await repo.get("api-app")
        assert retrieved is not None
        assert retrieved.slug == "api-app"
        assert retrieved.name == "API Application"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, repo: MemoryContainerRepository) -> None:
        """Test getting a nonexistent container returns None."""
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo: MemoryContainerRepository) -> None:
        """Test listing all containers."""
        await repo.save(create_container(slug="container-1"))
        await repo.save(create_container(slug="container-2"))
        await repo.save(create_container(slug="container-3"))

        all_containers = await repo.list_all()
        assert len(all_containers) == 3

    @pytest.mark.asyncio
    async def test_delete(self, repo: MemoryContainerRepository) -> None:
        """Test deleting a container."""
        await repo.save(create_container(slug="to-delete"))
        assert await repo.get("to-delete") is not None

        result = await repo.delete("to-delete")
        assert result is True
        assert await repo.get("to-delete") is None

    @pytest.mark.asyncio
    async def test_clear(self, repo: MemoryContainerRepository) -> None:
        """Test clearing all containers."""
        await repo.save(create_container(slug="container-1"))
        await repo.save(create_container(slug="container-2"))
        assert len(await repo.list_all()) == 2

        await repo.clear()
        assert len(await repo.list_all()) == 0


class TestMemoryContainerRepositoryQueries:
    """Test container-specific query methods."""

    @pytest.fixture
    def repo(self) -> MemoryContainerRepository:
        """Create a repository."""
        return MemoryContainerRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryContainerRepository
    ) -> MemoryContainerRepository:
        """Create a repository with sample data."""
        containers = [
            create_container(
                slug="api-app",
                name="API Application",
                system_slug="banking-system",
                container_type=ContainerType.API,
                tags=["backend"],
                docname="containers/api",
            ),
            create_container(
                slug="web-app",
                name="Web Application",
                system_slug="banking-system",
                container_type=ContainerType.WEB_APPLICATION,
                tags=["frontend"],
                docname="containers/web",
            ),
            create_container(
                slug="database",
                name="Database",
                system_slug="banking-system",
                container_type=ContainerType.DATABASE,
                tags=["data"],
                docname="containers/db",
            ),
            create_container(
                slug="analytics-api",
                name="Analytics API",
                system_slug="analytics-system",
                container_type=ContainerType.API,
                tags=["backend", "analytics"],
                docname="containers/analytics",
            ),
        ]
        for container in containers:
            await repo.save(container)
        return repo

    @pytest.mark.asyncio
    async def test_get_by_system(
        self, populated_repo: MemoryContainerRepository
    ) -> None:
        """Test getting containers by system."""
        banking_containers = await populated_repo.get_by_system("banking-system")
        assert len(banking_containers) == 3
        assert all(c.system_slug == "banking-system" for c in banking_containers)

    @pytest.mark.asyncio
    async def test_get_by_system_empty(
        self, populated_repo: MemoryContainerRepository
    ) -> None:
        """Test getting containers for system with none."""
        containers = await populated_repo.get_by_system("nonexistent")
        assert len(containers) == 0

    @pytest.mark.asyncio
    async def test_get_by_type(
        self, populated_repo: MemoryContainerRepository
    ) -> None:
        """Test getting containers by type."""
        apis = await populated_repo.get_by_type(ContainerType.API)
        assert len(apis) == 2
        assert all(c.container_type == ContainerType.API for c in apis)

    @pytest.mark.asyncio
    async def test_get_data_stores(
        self, populated_repo: MemoryContainerRepository
    ) -> None:
        """Test getting data store containers."""
        data_stores = await populated_repo.get_data_stores()
        assert len(data_stores) == 1
        assert data_stores[0].slug == "database"

    @pytest.mark.asyncio
    async def test_get_data_stores_filtered_by_system(
        self, populated_repo: MemoryContainerRepository
    ) -> None:
        """Test getting data stores filtered by system."""
        data_stores = await populated_repo.get_data_stores(
            system_slug="banking-system"
        )
        assert len(data_stores) == 1

        # No data stores in analytics system
        data_stores = await populated_repo.get_data_stores(
            system_slug="analytics-system"
        )
        assert len(data_stores) == 0

    @pytest.mark.asyncio
    async def test_get_applications(
        self, populated_repo: MemoryContainerRepository
    ) -> None:
        """Test getting application containers."""
        apps = await populated_repo.get_applications()
        assert len(apps) == 3
        assert all(c.is_application for c in apps)

    @pytest.mark.asyncio
    async def test_get_applications_filtered_by_system(
        self, populated_repo: MemoryContainerRepository
    ) -> None:
        """Test getting applications filtered by system."""
        apps = await populated_repo.get_applications(system_slug="banking-system")
        assert len(apps) == 2
        slugs = {c.slug for c in apps}
        assert slugs == {"api-app", "web-app"}

    @pytest.mark.asyncio
    async def test_get_by_tag(
        self, populated_repo: MemoryContainerRepository
    ) -> None:
        """Test getting containers by tag."""
        backend_containers = await populated_repo.get_by_tag("backend")
        assert len(backend_containers) == 2
        slugs = {c.slug for c in backend_containers}
        assert slugs == {"api-app", "analytics-api"}

    @pytest.mark.asyncio
    async def test_get_by_docname(
        self, populated_repo: MemoryContainerRepository
    ) -> None:
        """Test getting containers by docname."""
        containers = await populated_repo.get_by_docname("containers/api")
        assert len(containers) == 1
        assert containers[0].slug == "api-app"

    @pytest.mark.asyncio
    async def test_clear_by_docname(
        self, populated_repo: MemoryContainerRepository
    ) -> None:
        """Test clearing containers by docname."""
        count = await populated_repo.clear_by_docname("containers/api")
        assert count == 1

        remaining = await populated_repo.list_all()
        assert len(remaining) == 3
        assert all(c.slug != "api-app" for c in remaining)
