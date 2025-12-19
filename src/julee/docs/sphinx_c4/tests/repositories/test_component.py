"""Tests for MemoryComponentRepository."""

import pytest

from julee.docs.sphinx_c4.domain.models.component import Component
from julee.docs.sphinx_c4.repositories.memory.component import (
    MemoryComponentRepository,
)


def create_component(
    slug: str = "test-component",
    name: str = "Test Component",
    container_slug: str = "test-container",
    system_slug: str = "test-system",
    code_path: str = "",
    tags: list[str] | None = None,
    docname: str = "",
) -> Component:
    """Helper to create test components."""
    return Component(
        slug=slug,
        name=name,
        container_slug=container_slug,
        system_slug=system_slug,
        code_path=code_path,
        tags=tags or [],
        docname=docname,
    )


class TestMemoryComponentRepositoryBasicOperations:
    """Test basic CRUD operations."""

    @pytest.fixture
    def repo(self) -> MemoryComponentRepository:
        """Create a fresh repository."""
        return MemoryComponentRepository()

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo: MemoryComponentRepository) -> None:
        """Test saving and retrieving a component."""
        component = create_component(slug="auth-controller", name="Auth Controller")
        await repo.save(component)

        retrieved = await repo.get("auth-controller")
        assert retrieved is not None
        assert retrieved.slug == "auth-controller"
        assert retrieved.name == "Auth Controller"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, repo: MemoryComponentRepository) -> None:
        """Test getting a nonexistent component returns None."""
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo: MemoryComponentRepository) -> None:
        """Test listing all components."""
        await repo.save(create_component(slug="comp-1"))
        await repo.save(create_component(slug="comp-2"))
        await repo.save(create_component(slug="comp-3"))

        all_components = await repo.list_all()
        assert len(all_components) == 3

    @pytest.mark.asyncio
    async def test_delete(self, repo: MemoryComponentRepository) -> None:
        """Test deleting a component."""
        await repo.save(create_component(slug="to-delete"))
        assert await repo.get("to-delete") is not None

        result = await repo.delete("to-delete")
        assert result is True
        assert await repo.get("to-delete") is None

    @pytest.mark.asyncio
    async def test_clear(self, repo: MemoryComponentRepository) -> None:
        """Test clearing all components."""
        await repo.save(create_component(slug="comp-1"))
        await repo.save(create_component(slug="comp-2"))
        assert len(await repo.list_all()) == 2

        await repo.clear()
        assert len(await repo.list_all()) == 0


class TestMemoryComponentRepositoryQueries:
    """Test component-specific query methods."""

    @pytest.fixture
    def repo(self) -> MemoryComponentRepository:
        """Create a repository."""
        return MemoryComponentRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryComponentRepository
    ) -> MemoryComponentRepository:
        """Create a repository with sample data."""
        components = [
            create_component(
                slug="auth-controller",
                name="Auth Controller",
                container_slug="api-app",
                system_slug="banking-system",
                code_path="src/auth/controller.py",
                tags=["auth", "security"],
                docname="components/auth",
            ),
            create_component(
                slug="user-service",
                name="User Service",
                container_slug="api-app",
                system_slug="banking-system",
                code_path="src/user/service.py",
                tags=["user", "domain"],
                docname="components/user",
            ),
            create_component(
                slug="payment-processor",
                name="Payment Processor",
                container_slug="payment-service",
                system_slug="banking-system",
                tags=["payment"],
                docname="components/payment",
            ),
            create_component(
                slug="analytics-collector",
                name="Analytics Collector",
                container_slug="analytics-api",
                system_slug="analytics-system",
                tags=["analytics"],
                docname="components/analytics",
            ),
        ]
        for component in components:
            await repo.save(component)
        return repo

    @pytest.mark.asyncio
    async def test_get_by_container(
        self, populated_repo: MemoryComponentRepository
    ) -> None:
        """Test getting components by container."""
        api_components = await populated_repo.get_by_container("api-app")
        assert len(api_components) == 2
        assert all(c.container_slug == "api-app" for c in api_components)

    @pytest.mark.asyncio
    async def test_get_by_container_empty(
        self, populated_repo: MemoryComponentRepository
    ) -> None:
        """Test getting components for container with none."""
        components = await populated_repo.get_by_container("nonexistent")
        assert len(components) == 0

    @pytest.mark.asyncio
    async def test_get_by_system(
        self, populated_repo: MemoryComponentRepository
    ) -> None:
        """Test getting components by system."""
        banking_components = await populated_repo.get_by_system("banking-system")
        assert len(banking_components) == 3
        assert all(c.system_slug == "banking-system" for c in banking_components)

    @pytest.mark.asyncio
    async def test_get_with_code(
        self, populated_repo: MemoryComponentRepository
    ) -> None:
        """Test getting components with code paths."""
        components_with_code = await populated_repo.get_with_code()
        assert len(components_with_code) == 2
        assert all(c.code_path for c in components_with_code)

    @pytest.mark.asyncio
    async def test_get_by_tag(self, populated_repo: MemoryComponentRepository) -> None:
        """Test getting components by tag."""
        auth_components = await populated_repo.get_by_tag("auth")
        assert len(auth_components) == 1
        assert auth_components[0].slug == "auth-controller"

    @pytest.mark.asyncio
    async def test_get_by_docname(
        self, populated_repo: MemoryComponentRepository
    ) -> None:
        """Test getting components by docname."""
        components = await populated_repo.get_by_docname("components/auth")
        assert len(components) == 1
        assert components[0].slug == "auth-controller"

    @pytest.mark.asyncio
    async def test_clear_by_docname(
        self, populated_repo: MemoryComponentRepository
    ) -> None:
        """Test clearing components by docname."""
        count = await populated_repo.clear_by_docname("components/auth")
        assert count == 1

        remaining = await populated_repo.list_all()
        assert len(remaining) == 3
        assert all(c.slug != "auth-controller" for c in remaining)
