"""Tests for SoftwareSystem CRUD use cases."""

import pytest

from julee.c4.domain.models.software_system import (
    SoftwareSystem,
    SystemType,
)
from julee.c4.domain.use_cases.requests import (
    CreateSoftwareSystemRequest,
    DeleteSoftwareSystemRequest,
    GetSoftwareSystemRequest,
    ListSoftwareSystemsRequest,
    UpdateSoftwareSystemRequest,
)
from julee.c4.domain.use_cases.software_system import (
    CreateSoftwareSystemUseCase,
    DeleteSoftwareSystemUseCase,
    GetSoftwareSystemUseCase,
    ListSoftwareSystemsUseCase,
    UpdateSoftwareSystemUseCase,
)
from julee.c4.repositories.memory.software_system import (
    MemorySoftwareSystemRepository,
)


class TestCreateSoftwareSystemUseCase:
    """Test creating software systems."""

    @pytest.fixture
    def repo(self) -> MemorySoftwareSystemRepository:
        """Create a fresh repository."""
        return MemorySoftwareSystemRepository()

    @pytest.fixture
    def use_case(
        self, repo: MemorySoftwareSystemRepository
    ) -> CreateSoftwareSystemUseCase:
        """Create the use case with repository."""
        return CreateSoftwareSystemUseCase(repo)

    @pytest.mark.asyncio
    async def test_create_system_success(
        self,
        use_case: CreateSoftwareSystemUseCase,
        repo: MemorySoftwareSystemRepository,
    ) -> None:
        """Test successfully creating a software system."""
        request = CreateSoftwareSystemRequest(
            slug="banking-system",
            name="Internet Banking System",
            description="Allows customers to manage accounts",
            system_type="internal",
            owner="Digital Team",
            tags=["core", "finance"],
        )

        response = await use_case.execute(request)

        assert response.software_system is not None
        assert response.software_system.slug == "banking-system"
        assert response.software_system.name == "Internet Banking System"
        assert response.software_system.system_type == SystemType.INTERNAL

        # Verify it's persisted
        stored = await repo.get("banking-system")
        assert stored is not None
        assert stored.name == "Internet Banking System"

    @pytest.mark.asyncio
    async def test_create_system_with_defaults(
        self, use_case: CreateSoftwareSystemUseCase
    ) -> None:
        """Test creating with minimal required fields uses defaults."""
        request = CreateSoftwareSystemRequest(
            slug="simple-system",
            name="Simple System",
        )

        response = await use_case.execute(request)

        assert response.software_system.description == ""
        assert response.software_system.system_type == SystemType.INTERNAL
        assert response.software_system.tags == []


class TestGetSoftwareSystemUseCase:
    """Test getting software systems."""

    @pytest.fixture
    def repo(self) -> MemorySoftwareSystemRepository:
        """Create a fresh repository."""
        return MemorySoftwareSystemRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemorySoftwareSystemRepository
    ) -> MemorySoftwareSystemRepository:
        """Create repository with sample data."""
        await repo.save(
            SoftwareSystem(
                slug="banking-system",
                name="Banking System",
                system_type=SystemType.INTERNAL,
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemorySoftwareSystemRepository
    ) -> GetSoftwareSystemUseCase:
        """Create the use case with populated repository."""
        return GetSoftwareSystemUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_get_existing_system(
        self, use_case: GetSoftwareSystemUseCase
    ) -> None:
        """Test getting an existing software system."""
        request = GetSoftwareSystemRequest(slug="banking-system")

        response = await use_case.execute(request)

        assert response.software_system is not None
        assert response.software_system.slug == "banking-system"
        assert response.software_system.name == "Banking System"

    @pytest.mark.asyncio
    async def test_get_nonexistent_system(
        self, use_case: GetSoftwareSystemUseCase
    ) -> None:
        """Test getting a nonexistent system returns None."""
        request = GetSoftwareSystemRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.software_system is None


class TestListSoftwareSystemsUseCase:
    """Test listing software systems."""

    @pytest.fixture
    def repo(self) -> MemorySoftwareSystemRepository:
        """Create a fresh repository."""
        return MemorySoftwareSystemRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemorySoftwareSystemRepository
    ) -> MemorySoftwareSystemRepository:
        """Create repository with sample data."""
        systems = [
            SoftwareSystem(slug="system-1", name="System 1"),
            SoftwareSystem(slug="system-2", name="System 2"),
            SoftwareSystem(slug="system-3", name="System 3"),
        ]
        for s in systems:
            await repo.save(s)
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemorySoftwareSystemRepository
    ) -> ListSoftwareSystemsUseCase:
        """Create the use case with populated repository."""
        return ListSoftwareSystemsUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_list_all_systems(self, use_case: ListSoftwareSystemsUseCase) -> None:
        """Test listing all software systems."""
        request = ListSoftwareSystemsRequest()

        response = await use_case.execute(request)

        assert len(response.software_systems) == 3
        slugs = {s.slug for s in response.software_systems}
        assert slugs == {"system-1", "system-2", "system-3"}

    @pytest.mark.asyncio
    async def test_list_empty_repo(self, repo: MemorySoftwareSystemRepository) -> None:
        """Test listing returns empty list when no systems."""
        use_case = ListSoftwareSystemsUseCase(repo)
        request = ListSoftwareSystemsRequest()

        response = await use_case.execute(request)

        assert response.software_systems == []


class TestUpdateSoftwareSystemUseCase:
    """Test updating software systems."""

    @pytest.fixture
    def repo(self) -> MemorySoftwareSystemRepository:
        """Create a fresh repository."""
        return MemorySoftwareSystemRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemorySoftwareSystemRepository
    ) -> MemorySoftwareSystemRepository:
        """Create repository with sample data."""
        await repo.save(
            SoftwareSystem(
                slug="banking-system",
                name="Banking System",
                description="Original description",
                system_type=SystemType.INTERNAL,
                owner="Original Team",
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemorySoftwareSystemRepository
    ) -> UpdateSoftwareSystemUseCase:
        """Create the use case with populated repository."""
        return UpdateSoftwareSystemUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_update_single_field(
        self,
        use_case: UpdateSoftwareSystemUseCase,
        populated_repo: MemorySoftwareSystemRepository,
    ) -> None:
        """Test updating a single field."""
        request = UpdateSoftwareSystemRequest(
            slug="banking-system",
            name="Updated Banking System",
        )

        response = await use_case.execute(request)

        assert response.software_system is not None
        assert response.software_system.name == "Updated Banking System"
        # Other fields unchanged
        assert response.software_system.description == "Original description"
        assert response.software_system.owner == "Original Team"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(
        self, use_case: UpdateSoftwareSystemUseCase
    ) -> None:
        """Test updating multiple fields."""
        request = UpdateSoftwareSystemRequest(
            slug="banking-system",
            description="New description",
            owner="New Team",
            system_type="external",
        )

        response = await use_case.execute(request)

        assert response.software_system.description == "New description"
        assert response.software_system.owner == "New Team"
        assert response.software_system.system_type == SystemType.EXTERNAL

    @pytest.mark.asyncio
    async def test_update_nonexistent_system(
        self, use_case: UpdateSoftwareSystemUseCase
    ) -> None:
        """Test updating nonexistent system returns None."""
        request = UpdateSoftwareSystemRequest(
            slug="nonexistent",
            name="New Name",
        )

        response = await use_case.execute(request)

        assert response.software_system is None


class TestDeleteSoftwareSystemUseCase:
    """Test deleting software systems."""

    @pytest.fixture
    def repo(self) -> MemorySoftwareSystemRepository:
        """Create a fresh repository."""
        return MemorySoftwareSystemRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemorySoftwareSystemRepository
    ) -> MemorySoftwareSystemRepository:
        """Create repository with sample data."""
        await repo.save(SoftwareSystem(slug="to-delete", name="To Delete"))
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemorySoftwareSystemRepository
    ) -> DeleteSoftwareSystemUseCase:
        """Create the use case with populated repository."""
        return DeleteSoftwareSystemUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_delete_existing_system(
        self,
        use_case: DeleteSoftwareSystemUseCase,
        populated_repo: MemorySoftwareSystemRepository,
    ) -> None:
        """Test successfully deleting a software system."""
        request = DeleteSoftwareSystemRequest(slug="to-delete")

        response = await use_case.execute(request)

        assert response.deleted is True

        # Verify it's removed
        stored = await populated_repo.get("to-delete")
        assert stored is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_system(
        self, use_case: DeleteSoftwareSystemUseCase
    ) -> None:
        """Test deleting nonexistent system returns False."""
        request = DeleteSoftwareSystemRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.deleted is False
