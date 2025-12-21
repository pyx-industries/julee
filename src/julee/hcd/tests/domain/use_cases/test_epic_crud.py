"""Tests for Epic CRUD use cases."""

import pytest

from julee.hcd.domain.use_cases.requests import (
    CreateEpicRequest,
    DeleteEpicRequest,
    GetEpicRequest,
    ListEpicsRequest,
    UpdateEpicRequest,
)
from julee.hcd.domain.models.epic import Epic
from julee.hcd.domain.use_cases.epic import (
    CreateEpicUseCase,
    DeleteEpicUseCase,
    GetEpicUseCase,
    ListEpicsUseCase,
    UpdateEpicUseCase,
)
from julee.hcd.repositories.memory.epic import MemoryEpicRepository


class TestCreateEpicUseCase:
    """Test creating epics."""

    @pytest.fixture
    def repo(self) -> MemoryEpicRepository:
        """Create a fresh repository."""
        return MemoryEpicRepository()

    @pytest.fixture
    def use_case(self, repo: MemoryEpicRepository) -> CreateEpicUseCase:
        """Create the use case with repository."""
        return CreateEpicUseCase(repo)

    @pytest.mark.asyncio
    async def test_create_epic_success(
        self,
        use_case: CreateEpicUseCase,
        repo: MemoryEpicRepository,
    ) -> None:
        """Test successfully creating an epic."""
        request = CreateEpicRequest(
            slug="authentication",
            description="All authentication related stories",
            story_refs=["login-story", "logout-story", "password-reset"],
        )

        response = await use_case.execute(request)

        assert response.epic is not None
        assert response.epic.slug == "authentication"
        assert response.epic.description == "All authentication related stories"
        assert len(response.epic.story_refs) == 3

        # Verify it's persisted
        stored = await repo.get("authentication")
        assert stored is not None
        assert stored.slug == "authentication"

    @pytest.mark.asyncio
    async def test_create_epic_with_defaults(self, use_case: CreateEpicUseCase) -> None:
        """Test creating epic with default values."""
        request = CreateEpicRequest(slug="minimal-epic")

        response = await use_case.execute(request)

        assert response.epic.description == ""
        assert response.epic.story_refs == []


class TestGetEpicUseCase:
    """Test getting epics."""

    @pytest.fixture
    def repo(self) -> MemoryEpicRepository:
        """Create a fresh repository."""
        return MemoryEpicRepository()

    @pytest.fixture
    async def populated_repo(self, repo: MemoryEpicRepository) -> MemoryEpicRepository:
        """Create repository with sample data."""
        await repo.save(
            Epic(
                slug="test-epic",
                description="Test epic description",
                story_refs=["story-1", "story-2"],
            )
        )
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryEpicRepository) -> GetEpicUseCase:
        """Create the use case with populated repository."""
        return GetEpicUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_get_existing_epic(self, use_case: GetEpicUseCase) -> None:
        """Test getting an existing epic."""
        request = GetEpicRequest(slug="test-epic")

        response = await use_case.execute(request)

        assert response.epic is not None
        assert response.epic.slug == "test-epic"
        assert response.epic.description == "Test epic description"

    @pytest.mark.asyncio
    async def test_get_nonexistent_epic(self, use_case: GetEpicUseCase) -> None:
        """Test getting a nonexistent epic returns None."""
        request = GetEpicRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.epic is None


class TestListEpicsUseCase:
    """Test listing epics."""

    @pytest.fixture
    def repo(self) -> MemoryEpicRepository:
        """Create a fresh repository."""
        return MemoryEpicRepository()

    @pytest.fixture
    async def populated_repo(self, repo: MemoryEpicRepository) -> MemoryEpicRepository:
        """Create repository with sample data."""
        epics = [
            Epic(slug="epic-1", description="First epic"),
            Epic(slug="epic-2", description="Second epic"),
            Epic(slug="epic-3", description="Third epic"),
        ]
        for epic in epics:
            await repo.save(epic)
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryEpicRepository) -> ListEpicsUseCase:
        """Create the use case with populated repository."""
        return ListEpicsUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_list_all_epics(self, use_case: ListEpicsUseCase) -> None:
        """Test listing all epics."""
        request = ListEpicsRequest()

        response = await use_case.execute(request)

        assert len(response.epics) == 3
        slugs = {e.slug for e in response.epics}
        assert slugs == {"epic-1", "epic-2", "epic-3"}

    @pytest.mark.asyncio
    async def test_list_empty_repo(self, repo: MemoryEpicRepository) -> None:
        """Test listing returns empty list when no epics."""
        use_case = ListEpicsUseCase(repo)
        request = ListEpicsRequest()

        response = await use_case.execute(request)

        assert response.epics == []


class TestUpdateEpicUseCase:
    """Test updating epics."""

    @pytest.fixture
    def repo(self) -> MemoryEpicRepository:
        """Create a fresh repository."""
        return MemoryEpicRepository()

    @pytest.fixture
    async def populated_repo(self, repo: MemoryEpicRepository) -> MemoryEpicRepository:
        """Create repository with sample data."""
        await repo.save(
            Epic(
                slug="update-epic",
                description="Original description",
                story_refs=["original-story"],
            )
        )
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryEpicRepository) -> UpdateEpicUseCase:
        """Create the use case with populated repository."""
        return UpdateEpicUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_update_description(self, use_case: UpdateEpicUseCase) -> None:
        """Test updating the description."""
        request = UpdateEpicRequest(
            slug="update-epic",
            description="Updated description",
        )

        response = await use_case.execute(request)

        assert response.epic is not None
        assert response.found is True
        assert response.epic.description == "Updated description"
        # story_refs unchanged
        assert response.epic.story_refs == ["original-story"]

    @pytest.mark.asyncio
    async def test_update_story_refs(self, use_case: UpdateEpicUseCase) -> None:
        """Test updating story refs."""
        request = UpdateEpicRequest(
            slug="update-epic",
            story_refs=["new-story-1", "new-story-2"],
        )

        response = await use_case.execute(request)

        assert response.epic.story_refs == ["new-story-1", "new-story-2"]

    @pytest.mark.asyncio
    async def test_update_nonexistent_epic(self, use_case: UpdateEpicUseCase) -> None:
        """Test updating nonexistent epic returns None."""
        request = UpdateEpicRequest(
            slug="nonexistent",
            description="New description",
        )

        response = await use_case.execute(request)

        assert response.epic is None
        assert response.found is False


class TestDeleteEpicUseCase:
    """Test deleting epics."""

    @pytest.fixture
    def repo(self) -> MemoryEpicRepository:
        """Create a fresh repository."""
        return MemoryEpicRepository()

    @pytest.fixture
    async def populated_repo(self, repo: MemoryEpicRepository) -> MemoryEpicRepository:
        """Create repository with sample data."""
        await repo.save(Epic(slug="to-delete", description="Epic to delete"))
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryEpicRepository) -> DeleteEpicUseCase:
        """Create the use case with populated repository."""
        return DeleteEpicUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_delete_existing_epic(
        self,
        use_case: DeleteEpicUseCase,
        populated_repo: MemoryEpicRepository,
    ) -> None:
        """Test successfully deleting an epic."""
        request = DeleteEpicRequest(slug="to-delete")

        response = await use_case.execute(request)

        assert response.deleted is True

        # Verify it's removed
        stored = await populated_repo.get("to-delete")
        assert stored is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_epic(self, use_case: DeleteEpicUseCase) -> None:
        """Test deleting nonexistent epic returns False."""
        request = DeleteEpicRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.deleted is False
