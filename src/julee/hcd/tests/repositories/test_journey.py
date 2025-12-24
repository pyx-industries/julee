"""Tests for MemoryJourneyRepository."""

import pytest
import pytest_asyncio

from julee.hcd.domain.models.journey import Journey, JourneyStep
from julee.hcd.repositories.memory.journey import MemoryJourneyRepository


def create_journey(
    slug: str = "test-journey",
    persona: str = "User",
    docname: str = "journeys/test",
    depends_on: list[str] | None = None,
    steps: list[JourneyStep] | None = None,
) -> Journey:
    """Helper to create test journeys."""
    return Journey(
        slug=slug,
        persona=persona,
        docname=docname,
        depends_on=depends_on or [],
        steps=steps or [],
    )


class TestMemoryJourneyRepositoryBasicOperations:
    """Test basic CRUD operations."""

    @pytest.fixture
    def repo(self) -> MemoryJourneyRepository:
        """Create a fresh repository."""
        return MemoryJourneyRepository()

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo: MemoryJourneyRepository) -> None:
        """Test saving and retrieving a journey."""
        journey = create_journey(slug="build-vocabulary")
        await repo.save(journey)

        retrieved = await repo.get("build-vocabulary")
        assert retrieved is not None
        assert retrieved.slug == "build-vocabulary"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, repo: MemoryJourneyRepository) -> None:
        """Test getting a nonexistent journey returns None."""
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo: MemoryJourneyRepository) -> None:
        """Test listing all journeys."""
        await repo.save(create_journey(slug="journey-1"))
        await repo.save(create_journey(slug="journey-2"))
        await repo.save(create_journey(slug="journey-3"))

        all_journeys = await repo.list_all()
        assert len(all_journeys) == 3
        slugs = {j.slug for j in all_journeys}
        assert slugs == {"journey-1", "journey-2", "journey-3"}

    @pytest.mark.asyncio
    async def test_delete(self, repo: MemoryJourneyRepository) -> None:
        """Test deleting a journey."""
        await repo.save(create_journey(slug="to-delete"))
        assert await repo.get("to-delete") is not None

        result = await repo.delete("to-delete")
        assert result is True
        assert await repo.get("to-delete") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, repo: MemoryJourneyRepository) -> None:
        """Test deleting a nonexistent journey."""
        result = await repo.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear(self, repo: MemoryJourneyRepository) -> None:
        """Test clearing all journeys."""
        await repo.save(create_journey(slug="journey-1"))
        await repo.save(create_journey(slug="journey-2"))
        assert len(await repo.list_all()) == 2

        await repo.clear()
        assert len(await repo.list_all()) == 0


class TestMemoryJourneyRepositoryQueries:
    """Test journey-specific query methods."""

    @pytest.fixture
    def repo(self) -> MemoryJourneyRepository:
        """Create a repository."""
        return MemoryJourneyRepository()

    @pytest_asyncio.fixture
    async def populated_repo(
        self, repo: MemoryJourneyRepository
    ) -> MemoryJourneyRepository:
        """Create a repository with sample journeys."""
        journeys = [
            create_journey(
                slug="build-vocabulary",
                persona="Knowledge Curator",
                docname="journeys/build-vocabulary",
                depends_on=["operate-pipelines"],
                steps=[
                    JourneyStep.story("Upload Document"),
                    JourneyStep.epic("vocabulary-management"),
                ],
            ),
            create_journey(
                slug="operate-pipelines",
                persona="Knowledge Curator",
                docname="journeys/operate-pipelines",
                steps=[
                    JourneyStep.story("Configure Pipeline"),
                ],
            ),
            create_journey(
                slug="analyze-data",
                persona="Analyst",
                docname="journeys/analyze-data",
                depends_on=["build-vocabulary", "operate-pipelines"],
                steps=[
                    JourneyStep.story("Run Analysis"),
                    JourneyStep.epic("vocabulary-management"),
                ],
            ),
            create_journey(
                slug="review-results",
                persona="Analyst",
                docname="journeys/review-results",
            ),
            create_journey(
                slug="admin-setup",
                persona="Administrator",
                docname="journeys/admin-setup",
            ),
        ]
        for journey in journeys:
            await repo.save(journey)
        return repo

    @pytest.mark.asyncio
    async def test_get_by_persona(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test getting journeys by persona."""
        journeys = await populated_repo.get_by_persona("Knowledge Curator")
        assert len(journeys) == 2
        slugs = {j.slug for j in journeys}
        assert slugs == {"build-vocabulary", "operate-pipelines"}

    @pytest.mark.asyncio
    async def test_get_by_persona_case_insensitive(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test persona matching is case-insensitive."""
        journeys = await populated_repo.get_by_persona("knowledge curator")
        assert len(journeys) == 2

    @pytest.mark.asyncio
    async def test_get_by_persona_no_results(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test getting journeys for persona with none."""
        journeys = await populated_repo.get_by_persona("Unknown Persona")
        assert len(journeys) == 0

    @pytest.mark.asyncio
    async def test_get_by_docname(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test getting journeys by document name."""
        journeys = await populated_repo.get_by_docname("journeys/build-vocabulary")
        assert len(journeys) == 1
        assert journeys[0].slug == "build-vocabulary"

    @pytest.mark.asyncio
    async def test_get_by_docname_no_results(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test getting journeys for unknown document."""
        journeys = await populated_repo.get_by_docname("unknown/document")
        assert len(journeys) == 0

    @pytest.mark.asyncio
    async def test_clear_by_docname(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test clearing journeys by document name."""
        count = await populated_repo.clear_by_docname("journeys/build-vocabulary")
        assert count == 1
        assert await populated_repo.get("build-vocabulary") is None
        # Other journeys should remain
        assert len(await populated_repo.list_all()) == 4

    @pytest.mark.asyncio
    async def test_clear_by_docname_none_found(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test clearing non-existent document returns 0."""
        count = await populated_repo.clear_by_docname("unknown/document")
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_dependents(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test getting journeys that depend on a journey."""
        dependents = await populated_repo.get_dependents("operate-pipelines")
        assert len(dependents) == 2
        slugs = {j.slug for j in dependents}
        assert slugs == {"build-vocabulary", "analyze-data"}

    @pytest.mark.asyncio
    async def test_get_dependents_none(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test getting dependents for journey with none."""
        dependents = await populated_repo.get_dependents("admin-setup")
        assert len(dependents) == 0

    @pytest.mark.asyncio
    async def test_get_dependencies(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test getting journeys that a journey depends on."""
        deps = await populated_repo.get_dependencies("analyze-data")
        assert len(deps) == 2
        slugs = {j.slug for j in deps}
        assert slugs == {"build-vocabulary", "operate-pipelines"}

    @pytest.mark.asyncio
    async def test_get_dependencies_nonexistent_journey(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test getting dependencies for nonexistent journey."""
        deps = await populated_repo.get_dependencies("nonexistent")
        assert len(deps) == 0

    @pytest.mark.asyncio
    async def test_get_all_personas(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test getting all unique personas."""
        personas = await populated_repo.get_all_personas()
        assert personas == {"knowledge curator", "analyst", "administrator"}

    @pytest.mark.asyncio
    async def test_get_with_story_ref(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test getting journeys with a story reference."""
        journeys = await populated_repo.get_with_story_ref("Upload Document")
        assert len(journeys) == 1
        assert journeys[0].slug == "build-vocabulary"

    @pytest.mark.asyncio
    async def test_get_with_story_ref_case_insensitive(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test story ref matching is case-insensitive."""
        journeys = await populated_repo.get_with_story_ref("upload document")
        assert len(journeys) == 1

    @pytest.mark.asyncio
    async def test_get_with_story_ref_none(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test getting journeys with nonexistent story."""
        journeys = await populated_repo.get_with_story_ref("Unknown Story")
        assert len(journeys) == 0

    @pytest.mark.asyncio
    async def test_get_with_epic_ref(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test getting journeys with an epic reference."""
        journeys = await populated_repo.get_with_epic_ref("vocabulary-management")
        assert len(journeys) == 2
        slugs = {j.slug for j in journeys}
        assert slugs == {"build-vocabulary", "analyze-data"}

    @pytest.mark.asyncio
    async def test_get_with_epic_ref_none(
        self, populated_repo: MemoryJourneyRepository
    ) -> None:
        """Test getting journeys with nonexistent epic."""
        journeys = await populated_repo.get_with_epic_ref("unknown-epic")
        assert len(journeys) == 0
