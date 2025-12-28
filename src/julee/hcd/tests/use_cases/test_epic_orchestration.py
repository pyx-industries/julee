"""Tests for EpicOrchestrationUseCase.

Tests the business logic for detecting epic orchestration conditions:
- Empty epic (no story_refs)
- Unknown story refs (story_refs not found in StoryRepository)
"""

import pytest

from julee.hcd.entities.epic import Epic
from julee.hcd.entities.story import Story
from julee.hcd.infrastructure.repositories.memory.story import MemoryStoryRepository
from julee.hcd.use_cases.epic_orchestration import (
    EpicOrchestrationRequest,
    EpicOrchestrationUseCase,
)


class TestEpicOrchestrationUseCase:
    """Test epic orchestration condition detection."""

    @pytest.fixture
    def story_repo(self) -> MemoryStoryRepository:
        """Create fresh story repository."""
        return MemoryStoryRepository()

    @pytest.fixture
    def use_case(self, story_repo: MemoryStoryRepository) -> EpicOrchestrationUseCase:
        """Create use case with repository."""
        return EpicOrchestrationUseCase(story_repo=story_repo)

    @pytest.fixture
    def sample_epic(self) -> Epic:
        """Create a sample epic with story refs."""
        return Epic(
            slug="authentication",
            description="User authentication features",
            story_refs=["User Login", "Password Reset"],
        )

    @pytest.fixture
    def empty_epic(self) -> Epic:
        """Create an empty epic (no story refs)."""
        return Epic(
            slug="empty-epic",
            description="An epic without stories",
            story_refs=[],
        )

    @pytest.mark.asyncio
    async def test_no_conditions_when_stories_exist(
        self,
        use_case: EpicOrchestrationUseCase,
        story_repo: MemoryStoryRepository,
        sample_epic: Epic,
    ) -> None:
        """Test no conditions when all story refs exist."""
        # Setup: Create stories matching epic refs
        for title in sample_epic.story_refs:
            story = Story.from_feature_file(
                feature_title=title,
                persona="User",
                i_want="do something",
                so_that="benefit",
                app_slug="app",
                file_path=f"features/{title.lower().replace(' ', '_')}.feature",
            )
            await story_repo.save(story)

        # Execute
        request = EpicOrchestrationRequest(epic=sample_epic)
        response = await use_case.execute(request)

        # Verify: No conditions
        assert len(response.conditions) == 0
        assert not response.has_empty_epic
        assert not response.has_unknown_story_refs

    @pytest.mark.asyncio
    async def test_empty_epic_condition(
        self,
        use_case: EpicOrchestrationUseCase,
        empty_epic: Epic,
    ) -> None:
        """Test empty epic condition is detected."""
        # Execute
        request = EpicOrchestrationRequest(epic=empty_epic)
        response = await use_case.execute(request)

        # Verify: Empty epic detected
        assert len(response.conditions) == 1
        assert response.has_empty_epic
        assert not response.has_unknown_story_refs

        condition = response.conditions[0]
        assert condition.condition == "empty_epic"
        assert condition.epic_slug == "empty-epic"

    @pytest.mark.asyncio
    async def test_unknown_story_refs_condition(
        self,
        use_case: EpicOrchestrationUseCase,
        sample_epic: Epic,
    ) -> None:
        """Test unknown story refs condition when stories don't exist."""
        # Execute (no stories in repo)
        request = EpicOrchestrationRequest(epic=sample_epic)
        response = await use_case.execute(request)

        # Verify: Unknown story refs detected
        assert len(response.conditions) == 1
        assert not response.has_empty_epic
        assert response.has_unknown_story_refs

        condition = response.conditions[0]
        assert condition.condition == "unknown_story_refs"
        assert condition.epic_slug == "authentication"
        assert set(condition.details["unknown_refs"]) == {"User Login", "Password Reset"}

    @pytest.mark.asyncio
    async def test_partial_unknown_story_refs(
        self,
        use_case: EpicOrchestrationUseCase,
        story_repo: MemoryStoryRepository,
        sample_epic: Epic,
    ) -> None:
        """Test only unknown refs are reported when some exist."""
        # Setup: Create only one of the stories
        story = Story.from_feature_file(
            feature_title="User Login",
            persona="User",
            i_want="log in",
            so_that="access my account",
            app_slug="app",
            file_path="features/login.feature",
        )
        await story_repo.save(story)

        # Execute
        request = EpicOrchestrationRequest(epic=sample_epic)
        response = await use_case.execute(request)

        # Verify: Only Password Reset is unknown
        assert response.has_unknown_story_refs
        condition = next(c for c in response.conditions if c.condition == "unknown_story_refs")
        assert condition.details["unknown_refs"] == ["Password Reset"]

    @pytest.mark.asyncio
    async def test_response_contains_original_epic(
        self,
        use_case: EpicOrchestrationUseCase,
        sample_epic: Epic,
    ) -> None:
        """Test response contains the original epic."""
        request = EpicOrchestrationRequest(epic=sample_epic)
        response = await use_case.execute(request)

        assert response.epic == sample_epic
