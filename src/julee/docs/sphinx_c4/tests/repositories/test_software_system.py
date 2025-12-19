"""Tests for MemorySoftwareSystemRepository."""

import pytest

from julee.docs.sphinx_c4.domain.models.software_system import (
    SoftwareSystem,
    SystemType,
)
from julee.docs.sphinx_c4.repositories.memory.software_system import (
    MemorySoftwareSystemRepository,
)


def create_system(
    slug: str = "test-system",
    name: str = "Test System",
    system_type: SystemType = SystemType.INTERNAL,
    owner: str = "",
    tags: list[str] | None = None,
    docname: str = "",
) -> SoftwareSystem:
    """Helper to create test systems."""
    return SoftwareSystem(
        slug=slug,
        name=name,
        system_type=system_type,
        owner=owner,
        tags=tags or [],
        docname=docname,
    )


class TestMemorySoftwareSystemRepositoryBasicOperations:
    """Test basic CRUD operations."""

    @pytest.fixture
    def repo(self) -> MemorySoftwareSystemRepository:
        """Create a fresh repository."""
        return MemorySoftwareSystemRepository()

    @pytest.mark.asyncio
    async def test_save_and_get(
        self, repo: MemorySoftwareSystemRepository
    ) -> None:
        """Test saving and retrieving a system."""
        system = create_system(slug="banking-system", name="Banking System")
        await repo.save(system)

        retrieved = await repo.get("banking-system")
        assert retrieved is not None
        assert retrieved.slug == "banking-system"
        assert retrieved.name == "Banking System"

    @pytest.mark.asyncio
    async def test_get_nonexistent(
        self, repo: MemorySoftwareSystemRepository
    ) -> None:
        """Test getting a nonexistent system returns None."""
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo: MemorySoftwareSystemRepository) -> None:
        """Test listing all systems."""
        await repo.save(create_system(slug="system-1", name="System 1"))
        await repo.save(create_system(slug="system-2", name="System 2"))
        await repo.save(create_system(slug="system-3", name="System 3"))

        all_systems = await repo.list_all()
        assert len(all_systems) == 3
        slugs = {s.slug for s in all_systems}
        assert slugs == {"system-1", "system-2", "system-3"}

    @pytest.mark.asyncio
    async def test_delete(self, repo: MemorySoftwareSystemRepository) -> None:
        """Test deleting a system."""
        await repo.save(create_system(slug="to-delete"))
        assert await repo.get("to-delete") is not None

        result = await repo.delete("to-delete")
        assert result is True
        assert await repo.get("to-delete") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(
        self, repo: MemorySoftwareSystemRepository
    ) -> None:
        """Test deleting a nonexistent system."""
        result = await repo.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear(self, repo: MemorySoftwareSystemRepository) -> None:
        """Test clearing all systems."""
        await repo.save(create_system(slug="system-1"))
        await repo.save(create_system(slug="system-2"))
        assert len(await repo.list_all()) == 2

        await repo.clear()
        assert len(await repo.list_all()) == 0


class TestMemorySoftwareSystemRepositoryQueries:
    """Test repository-specific query methods."""

    @pytest.fixture
    def repo(self) -> MemorySoftwareSystemRepository:
        """Create a repository."""
        return MemorySoftwareSystemRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemorySoftwareSystemRepository
    ) -> MemorySoftwareSystemRepository:
        """Create a repository with sample data."""
        systems = [
            create_system(
                slug="banking-system",
                name="Banking System",
                system_type=SystemType.INTERNAL,
                owner="Digital Team",
                tags=["core", "finance"],
                docname="systems/banking",
            ),
            create_system(
                slug="crm-system",
                name="CRM System",
                system_type=SystemType.EXTERNAL,
                owner="Sales Team",
                tags=["external"],
                docname="systems/crm",
            ),
            create_system(
                slug="legacy-erp",
                name="Legacy ERP",
                system_type=SystemType.EXISTING,
                owner="IT Operations",
                tags=["legacy", "core"],
                docname="systems/legacy",
            ),
            create_system(
                slug="analytics-platform",
                name="Analytics Platform",
                system_type=SystemType.INTERNAL,
                owner="Digital Team",
                tags=["analytics"],
                docname="systems/analytics",
            ),
        ]
        for system in systems:
            await repo.save(system)
        return repo

    @pytest.mark.asyncio
    async def test_get_by_type(
        self, populated_repo: MemorySoftwareSystemRepository
    ) -> None:
        """Test getting systems by type."""
        internal = await populated_repo.get_by_type(SystemType.INTERNAL)
        assert len(internal) == 2
        assert all(s.system_type == SystemType.INTERNAL for s in internal)

    @pytest.mark.asyncio
    async def test_get_internal_systems(
        self, populated_repo: MemorySoftwareSystemRepository
    ) -> None:
        """Test getting internal systems."""
        internal = await populated_repo.get_internal_systems()
        assert len(internal) == 2
        slugs = {s.slug for s in internal}
        assert slugs == {"banking-system", "analytics-platform"}

    @pytest.mark.asyncio
    async def test_get_external_systems(
        self, populated_repo: MemorySoftwareSystemRepository
    ) -> None:
        """Test getting external systems."""
        external = await populated_repo.get_external_systems()
        assert len(external) == 1
        assert external[0].slug == "crm-system"

    @pytest.mark.asyncio
    async def test_get_by_tag(
        self, populated_repo: MemorySoftwareSystemRepository
    ) -> None:
        """Test getting systems by tag."""
        core_systems = await populated_repo.get_by_tag("core")
        assert len(core_systems) == 2
        slugs = {s.slug for s in core_systems}
        assert slugs == {"banking-system", "legacy-erp"}

    @pytest.mark.asyncio
    async def test_get_by_tag_case_insensitive(
        self, populated_repo: MemorySoftwareSystemRepository
    ) -> None:
        """Test tag lookup is case-insensitive."""
        systems = await populated_repo.get_by_tag("CORE")
        assert len(systems) == 2

    @pytest.mark.asyncio
    async def test_get_by_owner(
        self, populated_repo: MemorySoftwareSystemRepository
    ) -> None:
        """Test getting systems by owner."""
        digital_systems = await populated_repo.get_by_owner("Digital Team")
        assert len(digital_systems) == 2
        slugs = {s.slug for s in digital_systems}
        assert slugs == {"banking-system", "analytics-platform"}

    @pytest.mark.asyncio
    async def test_get_by_owner_case_insensitive(
        self, populated_repo: MemorySoftwareSystemRepository
    ) -> None:
        """Test owner lookup is case-insensitive."""
        systems = await populated_repo.get_by_owner("digital team")
        assert len(systems) == 2

    @pytest.mark.asyncio
    async def test_get_by_docname(
        self, populated_repo: MemorySoftwareSystemRepository
    ) -> None:
        """Test getting systems by docname."""
        systems = await populated_repo.get_by_docname("systems/banking")
        assert len(systems) == 1
        assert systems[0].slug == "banking-system"

    @pytest.mark.asyncio
    async def test_clear_by_docname(
        self, populated_repo: MemorySoftwareSystemRepository
    ) -> None:
        """Test clearing systems by docname."""
        count = await populated_repo.clear_by_docname("systems/banking")
        assert count == 1

        remaining = await populated_repo.list_all()
        assert len(remaining) == 3
        assert all(s.slug != "banking-system" for s in remaining)
