"""Tests for MemoryIntegrationRepository."""

import pytest
import pytest_asyncio

from julee.hcd.entities.integration import (
    Direction,
    ExternalDependency,
    Integration,
)
from julee.hcd.repositories.memory.integration import (
    MemoryIntegrationRepository,
)


def create_integration(
    slug: str = "test-integration",
    module: str = "test_integration",
    name: str = "Test Integration",
    direction: Direction = Direction.BIDIRECTIONAL,
    depends_on: list[ExternalDependency] | None = None,
) -> Integration:
    """Helper to create test integrations."""
    return Integration(
        slug=slug,
        module=module,
        name=name,
        direction=direction,
        depends_on=depends_on or [],
        manifest_path=f"integrations/{module}/integration.yaml",
    )


class TestMemoryIntegrationRepositoryBasicOperations:
    """Test basic CRUD operations."""

    @pytest.fixture
    def repo(self) -> MemoryIntegrationRepository:
        """Create a fresh repository."""
        return MemoryIntegrationRepository()

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo: MemoryIntegrationRepository) -> None:
        """Test saving and retrieving an integration."""
        integration = create_integration(slug="data-sync")
        await repo.save(integration)

        retrieved = await repo.get("data-sync")
        assert retrieved is not None
        assert retrieved.slug == "data-sync"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, repo: MemoryIntegrationRepository) -> None:
        """Test getting a nonexistent integration returns None."""
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo: MemoryIntegrationRepository) -> None:
        """Test listing all integrations."""
        await repo.save(create_integration(slug="int-1", module="int_1"))
        await repo.save(create_integration(slug="int-2", module="int_2"))
        await repo.save(create_integration(slug="int-3", module="int_3"))

        all_integrations = await repo.list_all()
        assert len(all_integrations) == 3
        slugs = {i.slug for i in all_integrations}
        assert slugs == {"int-1", "int-2", "int-3"}

    @pytest.mark.asyncio
    async def test_delete(self, repo: MemoryIntegrationRepository) -> None:
        """Test deleting an integration."""
        await repo.save(create_integration(slug="to-delete", module="to_delete"))
        assert await repo.get("to-delete") is not None

        result = await repo.delete("to-delete")
        assert result is True
        assert await repo.get("to-delete") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, repo: MemoryIntegrationRepository) -> None:
        """Test deleting a nonexistent integration."""
        result = await repo.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear(self, repo: MemoryIntegrationRepository) -> None:
        """Test clearing all integrations."""
        await repo.save(create_integration(slug="int-1", module="int_1"))
        await repo.save(create_integration(slug="int-2", module="int_2"))
        assert len(await repo.list_all()) == 2

        await repo.clear()
        assert len(await repo.list_all()) == 0


class TestMemoryIntegrationRepositoryQueries:
    """Test integration-specific query methods."""

    @pytest.fixture
    def repo(self) -> MemoryIntegrationRepository:
        """Create a repository."""
        return MemoryIntegrationRepository()

    @pytest_asyncio.fixture
    async def populated_repo(
        self, repo: MemoryIntegrationRepository
    ) -> MemoryIntegrationRepository:
        """Create a repository with sample integrations."""
        integrations = [
            create_integration(
                slug="pilot-data",
                module="pilot_data",
                name="Pilot Data Collection",
                direction=Direction.INBOUND,
                depends_on=[ExternalDependency(name="Pilot API")],
            ),
            create_integration(
                slug="analytics-export",
                module="analytics_export",
                name="Analytics Export",
                direction=Direction.OUTBOUND,
                depends_on=[
                    ExternalDependency(name="AWS S3"),
                    ExternalDependency(name="Analytics Service"),
                ],
            ),
            create_integration(
                slug="data-sync",
                module="data_sync",
                name="Data Sync",
                direction=Direction.BIDIRECTIONAL,
                depends_on=[ExternalDependency(name="AWS S3")],
            ),
            create_integration(
                slug="notifications",
                module="notifications",
                name="Notifications",
                direction=Direction.OUTBOUND,
            ),
            create_integration(
                slug="file-import",
                module="file_import",
                name="File Import",
                direction=Direction.INBOUND,
            ),
        ]
        for integration in integrations:
            await repo.save(integration)
        return repo

    @pytest.mark.asyncio
    async def test_get_by_direction_inbound(
        self, populated_repo: MemoryIntegrationRepository
    ) -> None:
        """Test getting inbound integrations."""
        integrations = await populated_repo.get_by_direction(Direction.INBOUND)
        assert len(integrations) == 2
        assert all(i.direction == Direction.INBOUND for i in integrations)

    @pytest.mark.asyncio
    async def test_get_by_direction_outbound(
        self, populated_repo: MemoryIntegrationRepository
    ) -> None:
        """Test getting outbound integrations."""
        integrations = await populated_repo.get_by_direction(Direction.OUTBOUND)
        assert len(integrations) == 2
        assert all(i.direction == Direction.OUTBOUND for i in integrations)

    @pytest.mark.asyncio
    async def test_get_by_direction_bidirectional(
        self, populated_repo: MemoryIntegrationRepository
    ) -> None:
        """Test getting bidirectional integrations."""
        integrations = await populated_repo.get_by_direction(Direction.BIDIRECTIONAL)
        assert len(integrations) == 1
        assert integrations[0].slug == "data-sync"

    @pytest.mark.asyncio
    async def test_get_by_module(
        self, populated_repo: MemoryIntegrationRepository
    ) -> None:
        """Test getting integration by module name."""
        integration = await populated_repo.get_by_module("pilot_data")
        assert integration is not None
        assert integration.slug == "pilot-data"

    @pytest.mark.asyncio
    async def test_get_by_module_not_found(
        self, populated_repo: MemoryIntegrationRepository
    ) -> None:
        """Test getting integration by nonexistent module."""
        integration = await populated_repo.get_by_module("nonexistent")
        assert integration is None

    @pytest.mark.asyncio
    async def test_get_by_name(
        self, populated_repo: MemoryIntegrationRepository
    ) -> None:
        """Test getting integration by name."""
        integration = await populated_repo.get_by_name("Pilot Data Collection")
        assert integration is not None
        assert integration.slug == "pilot-data"

    @pytest.mark.asyncio
    async def test_get_by_name_case_insensitive(
        self, populated_repo: MemoryIntegrationRepository
    ) -> None:
        """Test name matching is case-insensitive."""
        integration = await populated_repo.get_by_name("pilot data collection")
        assert integration is not None
        assert integration.slug == "pilot-data"

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(
        self, populated_repo: MemoryIntegrationRepository
    ) -> None:
        """Test getting integration by nonexistent name."""
        integration = await populated_repo.get_by_name("Nonexistent Integration")
        assert integration is None

    @pytest.mark.asyncio
    async def test_get_all_directions(
        self, populated_repo: MemoryIntegrationRepository
    ) -> None:
        """Test getting all unique directions."""
        directions = await populated_repo.get_all_directions()
        assert directions == {
            Direction.INBOUND,
            Direction.OUTBOUND,
            Direction.BIDIRECTIONAL,
        }

    @pytest.mark.asyncio
    async def test_get_with_dependencies(
        self, populated_repo: MemoryIntegrationRepository
    ) -> None:
        """Test getting integrations with dependencies."""
        integrations = await populated_repo.get_with_dependencies()
        assert len(integrations) == 3
        slugs = {i.slug for i in integrations}
        assert slugs == {"pilot-data", "analytics-export", "data-sync"}

    @pytest.mark.asyncio
    async def test_get_by_dependency(
        self, populated_repo: MemoryIntegrationRepository
    ) -> None:
        """Test getting integrations by dependency name."""
        integrations = await populated_repo.get_by_dependency("AWS S3")
        assert len(integrations) == 2
        slugs = {i.slug for i in integrations}
        assert slugs == {"analytics-export", "data-sync"}

    @pytest.mark.asyncio
    async def test_get_by_dependency_case_insensitive(
        self, populated_repo: MemoryIntegrationRepository
    ) -> None:
        """Test dependency matching is case-insensitive."""
        integrations = await populated_repo.get_by_dependency("aws s3")
        assert len(integrations) == 2

    @pytest.mark.asyncio
    async def test_get_by_dependency_not_found(
        self, populated_repo: MemoryIntegrationRepository
    ) -> None:
        """Test getting integrations by nonexistent dependency."""
        integrations = await populated_repo.get_by_dependency("Unknown Service")
        assert len(integrations) == 0
