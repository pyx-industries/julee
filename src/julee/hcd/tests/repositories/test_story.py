"""Tests for MemoryStoryRepository."""

import pytest
import pytest_asyncio

from julee.hcd.entities.story import Story
from julee.hcd.repositories.memory.story import MemoryStoryRepository


def create_story(
    slug: str = "test",
    feature_title: str = "Test Feature",
    persona: str = "User",
    app_slug: str = "app",
) -> Story:
    """Helper to create test stories."""
    return Story(
        slug=slug,
        feature_title=feature_title,
        persona=persona,
        app_slug=app_slug,
        file_path=f"tests/e2e/{app_slug}/features/{slug}.feature",
    )


class TestMemoryStoryRepositoryBasicOperations:
    """Test basic CRUD operations."""

    @pytest.fixture
    def repo(self) -> MemoryStoryRepository:
        """Create a fresh repository."""
        return MemoryStoryRepository()

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo: MemoryStoryRepository) -> None:
        """Test saving and retrieving a story."""
        story = create_story(slug="submit-order")
        await repo.save(story)

        retrieved = await repo.get("submit-order")
        assert retrieved is not None
        assert retrieved.slug == "submit-order"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, repo: MemoryStoryRepository) -> None:
        """Test getting a nonexistent story returns None."""
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo: MemoryStoryRepository) -> None:
        """Test listing all stories."""
        await repo.save(create_story(slug="story-1"))
        await repo.save(create_story(slug="story-2"))
        await repo.save(create_story(slug="story-3"))

        all_stories = await repo.list_all()
        assert len(all_stories) == 3
        slugs = {s.slug for s in all_stories}
        assert slugs == {"story-1", "story-2", "story-3"}

    @pytest.mark.asyncio
    async def test_delete(self, repo: MemoryStoryRepository) -> None:
        """Test deleting a story."""
        await repo.save(create_story(slug="to-delete"))
        assert await repo.get("to-delete") is not None

        result = await repo.delete("to-delete")
        assert result is True
        assert await repo.get("to-delete") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, repo: MemoryStoryRepository) -> None:
        """Test deleting a nonexistent story."""
        result = await repo.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear(self, repo: MemoryStoryRepository) -> None:
        """Test clearing all stories."""
        await repo.save(create_story(slug="story-1"))
        await repo.save(create_story(slug="story-2"))
        assert len(await repo.list_all()) == 2

        await repo.clear()
        assert len(await repo.list_all()) == 0


class TestMemoryStoryRepositoryQueries:
    """Test story-specific query methods."""

    @pytest.fixture
    def repo(self) -> MemoryStoryRepository:
        """Create a repository with sample data."""
        return MemoryStoryRepository()

    @pytest_asyncio.fixture
    async def populated_repo(
        self, repo: MemoryStoryRepository
    ) -> MemoryStoryRepository:
        """Create a repository with sample stories."""
        stories = [
            create_story(
                slug="upload-doc",
                feature_title="Upload Document",
                persona="Staff Member",
                app_slug="staff-portal",
            ),
            create_story(
                slug="view-report",
                feature_title="View Report",
                persona="Staff Member",
                app_slug="staff-portal",
            ),
            create_story(
                slug="submit-order",
                feature_title="Submit Order",
                persona="Customer",
                app_slug="checkout-app",
            ),
            create_story(
                slug="track-order",
                feature_title="Track Order",
                persona="Customer",
                app_slug="checkout-app",
            ),
            create_story(
                slug="admin-config",
                feature_title="Admin Configuration",
                persona="Admin",
                app_slug="admin-portal",
            ),
        ]
        for story in stories:
            await repo.save(story)
        return repo

    @pytest.mark.asyncio
    async def test_get_by_app(self, populated_repo: MemoryStoryRepository) -> None:
        """Test getting stories by app."""
        stories = await populated_repo.get_by_app("staff-portal")
        assert len(stories) == 2
        assert all(s.app_slug == "staff-portal" for s in stories)

    @pytest.mark.asyncio
    async def test_get_by_app_case_insensitive(
        self, populated_repo: MemoryStoryRepository
    ) -> None:
        """Test app matching is case-insensitive."""
        stories = await populated_repo.get_by_app("Staff-Portal")
        assert len(stories) == 2

    @pytest.mark.asyncio
    async def test_get_by_app_no_results(
        self, populated_repo: MemoryStoryRepository
    ) -> None:
        """Test getting stories for app with no stories."""
        stories = await populated_repo.get_by_app("nonexistent-app")
        assert len(stories) == 0

    @pytest.mark.asyncio
    async def test_get_by_persona(self, populated_repo: MemoryStoryRepository) -> None:
        """Test getting stories by persona."""
        stories = await populated_repo.get_by_persona("Customer")
        assert len(stories) == 2
        assert all(s.persona == "Customer" for s in stories)

    @pytest.mark.asyncio
    async def test_get_by_persona_case_insensitive(
        self, populated_repo: MemoryStoryRepository
    ) -> None:
        """Test persona matching is case-insensitive."""
        stories = await populated_repo.get_by_persona("staff member")
        assert len(stories) == 2

    @pytest.mark.asyncio
    async def test_get_by_feature_title(
        self, populated_repo: MemoryStoryRepository
    ) -> None:
        """Test getting a story by feature title."""
        story = await populated_repo.get_by_feature_title("Upload Document")
        assert story is not None
        assert story.slug == "upload-doc"

    @pytest.mark.asyncio
    async def test_get_by_feature_title_case_insensitive(
        self, populated_repo: MemoryStoryRepository
    ) -> None:
        """Test feature title matching is case-insensitive."""
        story = await populated_repo.get_by_feature_title("upload document")
        assert story is not None
        assert story.slug == "upload-doc"

    @pytest.mark.asyncio
    async def test_get_by_feature_title_not_found(
        self, populated_repo: MemoryStoryRepository
    ) -> None:
        """Test getting story by nonexistent feature title."""
        story = await populated_repo.get_by_feature_title("Nonexistent Feature")
        assert story is None

    @pytest.mark.asyncio
    async def test_get_apps_with_stories(
        self, populated_repo: MemoryStoryRepository
    ) -> None:
        """Test getting apps that have stories."""
        apps = await populated_repo.get_apps_with_stories()
        assert apps == {"staff-portal", "checkout-app", "admin-portal"}

    @pytest.mark.asyncio
    async def test_get_all_personas(
        self, populated_repo: MemoryStoryRepository
    ) -> None:
        """Test getting all unique personas."""
        personas = await populated_repo.get_all_personas()
        assert personas == {"staff member", "customer", "admin"}

    @pytest.mark.asyncio
    async def test_get_all_personas_excludes_unknown(
        self, repo: MemoryStoryRepository
    ) -> None:
        """Test that 'unknown' persona is excluded from results."""
        await repo.save(
            Story(
                slug="test",
                feature_title="Test",
                persona="unknown",
                app_slug="app",
                file_path="test.feature",
            )
        )
        await repo.save(create_story(slug="known", persona="Known User"))

        personas = await repo.get_all_personas()
        assert "unknown" not in personas
        assert "known user" in personas
