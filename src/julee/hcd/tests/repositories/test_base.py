"""Tests for MemoryRepositoryMixin base utility methods."""

import pytest

from julee.hcd.entities.story import Story
from julee.hcd.infrastructure.repositories.memory.story import MemoryStoryRepository


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


class TestFindByField:
    """Test the find_by_field utility method from MemoryRepositoryMixin."""

    @pytest.fixture
    def repo(self) -> MemoryStoryRepository:
        """Create a fresh repository."""
        return MemoryStoryRepository()

    @pytest.mark.asyncio
    async def test_find_by_field_single_match(
        self, repo: MemoryStoryRepository
    ) -> None:
        """Test finding entities by a field with single match."""
        await repo.save(create_story(slug="story-1", persona="Admin"))
        await repo.save(create_story(slug="story-2", persona="User"))
        await repo.save(create_story(slug="story-3", persona="User"))

        result = await repo.find_by_field("persona", "Admin")

        assert len(result) == 1
        assert result[0].slug == "story-1"

    @pytest.mark.asyncio
    async def test_find_by_field_multiple_matches(
        self, repo: MemoryStoryRepository
    ) -> None:
        """Test finding entities by a field with multiple matches."""
        await repo.save(create_story(slug="story-1", app_slug="portal"))
        await repo.save(create_story(slug="story-2", app_slug="portal"))
        await repo.save(create_story(slug="story-3", app_slug="other"))

        result = await repo.find_by_field("app_slug", "portal")

        assert len(result) == 2
        slugs = {s.slug for s in result}
        assert slugs == {"story-1", "story-2"}

    @pytest.mark.asyncio
    async def test_find_by_field_no_matches(self, repo: MemoryStoryRepository) -> None:
        """Test finding entities by a field with no matches."""
        await repo.save(create_story(slug="story-1", persona="User"))

        result = await repo.find_by_field("persona", "Admin")

        assert result == []

    @pytest.mark.asyncio
    async def test_find_by_field_nonexistent_field(
        self, repo: MemoryStoryRepository
    ) -> None:
        """Test finding by a field that doesn't exist returns empty list."""
        await repo.save(create_story(slug="story-1"))

        result = await repo.find_by_field("nonexistent_field", "value")

        assert result == []


class TestFindByFieldIn:
    """Test the find_by_field_in utility method from MemoryRepositoryMixin."""

    @pytest.fixture
    def repo(self) -> MemoryStoryRepository:
        """Create a fresh repository."""
        return MemoryStoryRepository()

    @pytest.mark.asyncio
    async def test_find_by_field_in_multiple_values(
        self, repo: MemoryStoryRepository
    ) -> None:
        """Test finding entities where field is in a list of values."""
        await repo.save(create_story(slug="story-1", persona="Admin"))
        await repo.save(create_story(slug="story-2", persona="User"))
        await repo.save(create_story(slug="story-3", persona="Guest"))

        result = await repo.find_by_field_in("persona", ["Admin", "User"])

        assert len(result) == 2
        personas = {s.persona for s in result}
        assert personas == {"Admin", "User"}

    @pytest.mark.asyncio
    async def test_find_by_field_in_single_value(
        self, repo: MemoryStoryRepository
    ) -> None:
        """Test finding entities with single value in list."""
        await repo.save(create_story(slug="story-1", app_slug="portal"))
        await repo.save(create_story(slug="story-2", app_slug="other"))

        result = await repo.find_by_field_in("app_slug", ["portal"])

        assert len(result) == 1
        assert result[0].slug == "story-1"

    @pytest.mark.asyncio
    async def test_find_by_field_in_no_matches(
        self, repo: MemoryStoryRepository
    ) -> None:
        """Test finding entities with no matching values."""
        await repo.save(create_story(slug="story-1", persona="User"))

        result = await repo.find_by_field_in("persona", ["Admin", "Guest"])

        assert result == []

    @pytest.mark.asyncio
    async def test_find_by_field_in_empty_list(
        self, repo: MemoryStoryRepository
    ) -> None:
        """Test finding with empty values list returns empty result."""
        await repo.save(create_story(slug="story-1"))

        result = await repo.find_by_field_in("persona", [])

        assert result == []

    @pytest.mark.asyncio
    async def test_find_by_field_in_all_match(
        self, repo: MemoryStoryRepository
    ) -> None:
        """Test when all entities match."""
        await repo.save(create_story(slug="story-1", persona="Admin"))
        await repo.save(create_story(slug="story-2", persona="User"))

        result = await repo.find_by_field_in("persona", ["Admin", "User", "Guest"])

        assert len(result) == 2
