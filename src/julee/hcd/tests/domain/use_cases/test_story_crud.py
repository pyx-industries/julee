"""Tests for Story CRUD use cases."""

import pytest

from julee.hcd.domain.models.story import Story
from julee.hcd.domain.use_cases.story import (
    CreateStoryRequest,
    CreateStoryUseCase,
    DeleteStoryRequest,
    DeleteStoryUseCase,
    GetStoryRequest,
    GetStoryUseCase,
    ListStoriesRequest,
    ListStoriesUseCase,
    UpdateStoryRequest,
    UpdateStoryUseCase,
)
from julee.hcd.repositories.memory.story import MemoryStoryRepository


class TestCreateStoryUseCase:
    """Test creating stories."""

    @pytest.fixture
    def repo(self) -> MemoryStoryRepository:
        """Create a fresh repository."""
        return MemoryStoryRepository()

    @pytest.fixture
    def use_case(self, repo: MemoryStoryRepository) -> CreateStoryUseCase:
        """Create the use case with repository."""
        return CreateStoryUseCase(repo)

    @pytest.mark.asyncio
    async def test_create_story_success(
        self,
        use_case: CreateStoryUseCase,
        repo: MemoryStoryRepository,
    ) -> None:
        """Test successfully creating a story."""
        request = CreateStoryRequest(
            feature_title="User Login",
            persona="Customer",
            app_slug="portal",
            i_want="log in to my account",
            so_that="I can access my dashboard",
        )

        response = await use_case.execute(request)

        assert response.story is not None
        assert response.story.feature_title == "User Login"
        assert response.story.persona == "Customer"
        assert response.story.app_slug == "portal"
        assert response.story.i_want == "log in to my account"
        assert response.story.so_that == "I can access my dashboard"

        # Verify it's persisted
        stored = await repo.get(response.story.slug)
        assert stored is not None

    @pytest.mark.asyncio
    async def test_create_story_with_defaults(
        self, use_case: CreateStoryUseCase
    ) -> None:
        """Test creating story with default values."""
        request = CreateStoryRequest(
            feature_title="Simple Feature",
            persona="User",
            app_slug="app",
        )

        response = await use_case.execute(request)

        assert response.story.i_want == "do something"
        assert response.story.so_that == "achieve a goal"

    @pytest.mark.asyncio
    async def test_create_story_generates_slug(
        self, use_case: CreateStoryUseCase
    ) -> None:
        """Test that slug is generated from feature title and app slug."""
        request = CreateStoryRequest(
            feature_title="Complex Feature Name",
            persona="Admin",
            app_slug="admin-portal",
        )

        response = await use_case.execute(request)

        # Slug should be generated and not empty
        assert response.story.slug
        assert "complex-feature" in response.story.slug.lower()


class TestGetStoryUseCase:
    """Test getting stories."""

    @pytest.fixture
    def repo(self) -> MemoryStoryRepository:
        """Create a fresh repository."""
        return MemoryStoryRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryStoryRepository
    ) -> MemoryStoryRepository:
        """Create repository with sample data."""
        story = Story.from_feature_file(
            feature_title="Test Feature",
            persona="Tester",
            i_want="test things",
            so_that="quality improves",
            app_slug="test-app",
            file_path="features/test.feature",
        )
        await repo.save(story)
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryStoryRepository) -> GetStoryUseCase:
        """Create the use case with populated repository."""
        return GetStoryUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_get_existing_story(
        self, use_case: GetStoryUseCase, populated_repo: MemoryStoryRepository
    ) -> None:
        """Test getting an existing story."""
        stories = await populated_repo.list_all()
        slug = stories[0].slug

        request = GetStoryRequest(slug=slug)
        response = await use_case.execute(request)

        assert response.story is not None
        assert response.story.feature_title == "Test Feature"

    @pytest.mark.asyncio
    async def test_get_nonexistent_story(self, use_case: GetStoryUseCase) -> None:
        """Test getting a nonexistent story returns None."""
        request = GetStoryRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.story is None


class TestListStoriesUseCase:
    """Test listing stories."""

    @pytest.fixture
    def repo(self) -> MemoryStoryRepository:
        """Create a fresh repository."""
        return MemoryStoryRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryStoryRepository
    ) -> MemoryStoryRepository:
        """Create repository with sample data."""
        stories = [
            Story.from_feature_file(
                feature_title="Feature One",
                persona="User",
                i_want="do one",
                so_that="benefit one",
                app_slug="app1",
                file_path="features/one.feature",
            ),
            Story.from_feature_file(
                feature_title="Feature Two",
                persona="Admin",
                i_want="do two",
                so_that="benefit two",
                app_slug="app2",
                file_path="features/two.feature",
            ),
            Story.from_feature_file(
                feature_title="Feature Three",
                persona="User",
                i_want="do three",
                so_that="benefit three",
                app_slug="app1",
                file_path="features/three.feature",
            ),
        ]
        for story in stories:
            await repo.save(story)
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryStoryRepository) -> ListStoriesUseCase:
        """Create the use case with populated repository."""
        return ListStoriesUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_list_all_stories(self, use_case: ListStoriesUseCase) -> None:
        """Test listing all stories."""
        request = ListStoriesRequest()

        response = await use_case.execute(request)

        assert len(response.stories) == 3

    @pytest.mark.asyncio
    async def test_list_empty_repo(self, repo: MemoryStoryRepository) -> None:
        """Test listing returns empty list when no stories."""
        use_case = ListStoriesUseCase(repo)
        request = ListStoriesRequest()

        response = await use_case.execute(request)

        assert response.stories == []


class TestUpdateStoryUseCase:
    """Test updating stories."""

    @pytest.fixture
    def repo(self) -> MemoryStoryRepository:
        """Create a fresh repository."""
        return MemoryStoryRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryStoryRepository
    ) -> MemoryStoryRepository:
        """Create repository with sample data."""
        story = Story.from_feature_file(
            feature_title="Original Feature",
            persona="Original User",
            i_want="do the original thing",
            so_that="original benefit",
            app_slug="original-app",
            file_path="features/original.feature",
        )
        await repo.save(story)
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryStoryRepository) -> UpdateStoryUseCase:
        """Create the use case with populated repository."""
        return UpdateStoryUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_update_single_field(
        self,
        use_case: UpdateStoryUseCase,
        populated_repo: MemoryStoryRepository,
    ) -> None:
        """Test updating a single field."""
        stories = await populated_repo.list_all()
        slug = stories[0].slug

        request = UpdateStoryRequest(
            slug=slug,
            i_want="do something new",
        )

        response = await use_case.execute(request)

        assert response.story is not None
        assert response.found is True
        assert response.story.i_want == "do something new"
        # Other fields unchanged
        assert response.story.so_that == "original benefit"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(
        self,
        use_case: UpdateStoryUseCase,
        populated_repo: MemoryStoryRepository,
    ) -> None:
        """Test updating multiple fields."""
        stories = await populated_repo.list_all()
        slug = stories[0].slug

        request = UpdateStoryRequest(
            slug=slug,
            i_want="do multiple things",
            so_that="multiple benefits",
        )

        response = await use_case.execute(request)

        assert response.story.i_want == "do multiple things"
        assert response.story.so_that == "multiple benefits"

    @pytest.mark.asyncio
    async def test_update_nonexistent_story(self, use_case: UpdateStoryUseCase) -> None:
        """Test updating nonexistent story returns None."""
        request = UpdateStoryRequest(
            slug="nonexistent",
            i_want="new value",
        )

        response = await use_case.execute(request)

        assert response.story is None
        assert response.found is False


class TestDeleteStoryUseCase:
    """Test deleting stories."""

    @pytest.fixture
    def repo(self) -> MemoryStoryRepository:
        """Create a fresh repository."""
        return MemoryStoryRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryStoryRepository
    ) -> MemoryStoryRepository:
        """Create repository with sample data."""
        story = Story.from_feature_file(
            feature_title="To Delete",
            persona="User",
            i_want="delete something",
            so_that="it is gone",
            app_slug="app",
            file_path="features/delete.feature",
        )
        await repo.save(story)
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryStoryRepository) -> DeleteStoryUseCase:
        """Create the use case with populated repository."""
        return DeleteStoryUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_delete_existing_story(
        self,
        use_case: DeleteStoryUseCase,
        populated_repo: MemoryStoryRepository,
    ) -> None:
        """Test successfully deleting a story."""
        stories = await populated_repo.list_all()
        slug = stories[0].slug

        request = DeleteStoryRequest(slug=slug)

        response = await use_case.execute(request)

        assert response.deleted is True

        # Verify it's removed
        stored = await populated_repo.get(slug)
        assert stored is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_story(self, use_case: DeleteStoryUseCase) -> None:
        """Test deleting nonexistent story returns False."""
        request = DeleteStoryRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.deleted is False
