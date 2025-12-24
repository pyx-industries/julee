"""Tests for MemoryEpicRepository."""

import pytest
import pytest_asyncio

from julee.hcd.entities.epic import Epic
from julee.hcd.infrastructure.repositories.memory.epic import MemoryEpicRepository


def create_epic(
    slug: str = "test-epic",
    description: str = "Test description",
    docname: str = "epics/test",
    story_refs: list[str] | None = None,
) -> Epic:
    """Helper to create test epics."""
    return Epic(
        slug=slug,
        description=description,
        docname=docname,
        story_refs=story_refs or [],
    )


class TestMemoryEpicRepositoryBasicOperations:
    """Test basic CRUD operations."""

    @pytest.fixture
    def repo(self) -> MemoryEpicRepository:
        """Create a fresh repository."""
        return MemoryEpicRepository()

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo: MemoryEpicRepository) -> None:
        """Test saving and retrieving an epic."""
        epic = create_epic(slug="vocabulary-management")
        await repo.save(epic)

        retrieved = await repo.get("vocabulary-management")
        assert retrieved is not None
        assert retrieved.slug == "vocabulary-management"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, repo: MemoryEpicRepository) -> None:
        """Test getting a nonexistent epic returns None."""
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo: MemoryEpicRepository) -> None:
        """Test listing all epics."""
        await repo.save(create_epic(slug="epic-1"))
        await repo.save(create_epic(slug="epic-2"))
        await repo.save(create_epic(slug="epic-3"))

        all_epics = await repo.list_all()
        assert len(all_epics) == 3
        slugs = {e.slug for e in all_epics}
        assert slugs == {"epic-1", "epic-2", "epic-3"}

    @pytest.mark.asyncio
    async def test_delete(self, repo: MemoryEpicRepository) -> None:
        """Test deleting an epic."""
        await repo.save(create_epic(slug="to-delete"))
        assert await repo.get("to-delete") is not None

        result = await repo.delete("to-delete")
        assert result is True
        assert await repo.get("to-delete") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, repo: MemoryEpicRepository) -> None:
        """Test deleting a nonexistent epic."""
        result = await repo.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear(self, repo: MemoryEpicRepository) -> None:
        """Test clearing all epics."""
        await repo.save(create_epic(slug="epic-1"))
        await repo.save(create_epic(slug="epic-2"))
        assert len(await repo.list_all()) == 2

        await repo.clear()
        assert len(await repo.list_all()) == 0


class TestMemoryEpicRepositoryQueries:
    """Test epic-specific query methods."""

    @pytest.fixture
    def repo(self) -> MemoryEpicRepository:
        """Create a repository."""
        return MemoryEpicRepository()

    @pytest_asyncio.fixture
    async def populated_repo(self, repo: MemoryEpicRepository) -> MemoryEpicRepository:
        """Create a repository with sample epics."""
        epics = [
            create_epic(
                slug="vocabulary-management",
                description="Manage vocabulary catalogs",
                docname="epics/vocabulary",
                story_refs=["Upload Document", "Review Vocabulary", "Publish Catalog"],
            ),
            create_epic(
                slug="credential-creation",
                description="Create credentials",
                docname="epics/credentials",
                story_refs=["Create Credential", "Assign Credential"],
            ),
            create_epic(
                slug="pipeline-operations",
                description="Operate data pipelines",
                docname="epics/pipelines",
                story_refs=["Configure Pipeline", "Run Pipeline"],
            ),
            create_epic(
                slug="analytics",
                description="Analytics features",
                docname="epics/vocabulary",  # Same docname as vocabulary-management
                story_refs=["Review Vocabulary", "Generate Report"],
            ),
            create_epic(
                slug="empty-epic",
                description="Epic with no stories",
                docname="epics/empty",
            ),
        ]
        for epic in epics:
            await repo.save(epic)
        return repo

    @pytest.mark.asyncio
    async def test_get_by_docname(self, populated_repo: MemoryEpicRepository) -> None:
        """Test getting epics by document name."""
        epics = await populated_repo.get_by_docname("epics/vocabulary")
        assert len(epics) == 2
        slugs = {e.slug for e in epics}
        assert slugs == {"vocabulary-management", "analytics"}

    @pytest.mark.asyncio
    async def test_get_by_docname_single(
        self, populated_repo: MemoryEpicRepository
    ) -> None:
        """Test getting epics for document with one epic."""
        epics = await populated_repo.get_by_docname("epics/credentials")
        assert len(epics) == 1
        assert epics[0].slug == "credential-creation"

    @pytest.mark.asyncio
    async def test_get_by_docname_no_results(
        self, populated_repo: MemoryEpicRepository
    ) -> None:
        """Test getting epics for unknown document."""
        epics = await populated_repo.get_by_docname("unknown/document")
        assert len(epics) == 0

    @pytest.mark.asyncio
    async def test_clear_by_docname(self, populated_repo: MemoryEpicRepository) -> None:
        """Test clearing epics by document name."""
        count = await populated_repo.clear_by_docname("epics/vocabulary")
        assert count == 2
        assert await populated_repo.get("vocabulary-management") is None
        assert await populated_repo.get("analytics") is None
        # Other epics should remain
        assert len(await populated_repo.list_all()) == 3

    @pytest.mark.asyncio
    async def test_clear_by_docname_none_found(
        self, populated_repo: MemoryEpicRepository
    ) -> None:
        """Test clearing non-existent document returns 0."""
        count = await populated_repo.clear_by_docname("unknown/document")
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_with_story_ref(
        self, populated_repo: MemoryEpicRepository
    ) -> None:
        """Test getting epics with a story reference."""
        epics = await populated_repo.get_with_story_ref("Upload Document")
        assert len(epics) == 1
        assert epics[0].slug == "vocabulary-management"

    @pytest.mark.asyncio
    async def test_get_with_story_ref_multiple(
        self, populated_repo: MemoryEpicRepository
    ) -> None:
        """Test getting epics with a story in multiple epics."""
        epics = await populated_repo.get_with_story_ref("Review Vocabulary")
        assert len(epics) == 2
        slugs = {e.slug for e in epics}
        assert slugs == {"vocabulary-management", "analytics"}

    @pytest.mark.asyncio
    async def test_get_with_story_ref_case_insensitive(
        self, populated_repo: MemoryEpicRepository
    ) -> None:
        """Test story ref matching is case-insensitive."""
        epics = await populated_repo.get_with_story_ref("upload document")
        assert len(epics) == 1
        assert epics[0].slug == "vocabulary-management"

    @pytest.mark.asyncio
    async def test_get_with_story_ref_no_results(
        self, populated_repo: MemoryEpicRepository
    ) -> None:
        """Test getting epics with nonexistent story."""
        epics = await populated_repo.get_with_story_ref("Unknown Story")
        assert len(epics) == 0

    @pytest.mark.asyncio
    async def test_get_all_story_refs(
        self, populated_repo: MemoryEpicRepository
    ) -> None:
        """Test getting all unique story references."""
        refs = await populated_repo.get_all_story_refs()
        expected = {
            "upload document",
            "review vocabulary",
            "publish catalog",
            "create credential",
            "assign credential",
            "configure pipeline",
            "run pipeline",
            "generate report",
        }
        assert refs == expected

    @pytest.mark.asyncio
    async def test_get_all_story_refs_empty_repo(
        self, repo: MemoryEpicRepository
    ) -> None:
        """Test getting story refs from empty repository."""
        refs = await repo.get_all_story_refs()
        assert refs == set()
