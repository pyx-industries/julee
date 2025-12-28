"""Tests for StoryOrchestrationUseCase.

Tests the business logic for detecting story orchestration conditions:
- Unknown persona (story.persona not found in PersonaRepository)
- Orphan story (story not referenced in any Epic.story_refs)
"""

import pytest

from julee.hcd.entities.epic import Epic
from julee.hcd.entities.persona import Persona
from julee.hcd.entities.story import Story
from julee.hcd.infrastructure.repositories.memory.epic import MemoryEpicRepository
from julee.hcd.infrastructure.repositories.memory.persona import MemoryPersonaRepository
from julee.hcd.use_cases.story_orchestration import (
    StoryOrchestrationRequest,
    StoryOrchestrationUseCase,
)


class TestStoryOrchestrationUseCase:
    """Test story orchestration condition detection."""

    @pytest.fixture
    def persona_repo(self) -> MemoryPersonaRepository:
        """Create fresh persona repository."""
        return MemoryPersonaRepository()

    @pytest.fixture
    def epic_repo(self) -> MemoryEpicRepository:
        """Create fresh epic repository."""
        return MemoryEpicRepository()

    @pytest.fixture
    def use_case(
        self,
        persona_repo: MemoryPersonaRepository,
        epic_repo: MemoryEpicRepository,
    ) -> StoryOrchestrationUseCase:
        """Create use case with repositories."""
        return StoryOrchestrationUseCase(
            persona_repo=persona_repo,
            epic_repo=epic_repo,
        )

    @pytest.fixture
    def sample_story(self) -> Story:
        """Create a sample story for testing."""
        return Story.from_feature_file(
            feature_title="User Login",
            persona="Customer",
            i_want="log in to my account",
            so_that="I can access my dashboard",
            app_slug="portal",
            file_path="features/login.feature",
        )

    @pytest.mark.asyncio
    async def test_no_conditions_when_persona_exists_and_in_epic(
        self,
        use_case: StoryOrchestrationUseCase,
        persona_repo: MemoryPersonaRepository,
        epic_repo: MemoryEpicRepository,
        sample_story: Story,
    ) -> None:
        """Test no conditions when story has known persona and is in an epic."""
        # Setup: Known persona
        persona = Persona.from_story_reference("Customer")
        await persona_repo.save(persona)

        # Setup: Epic containing this story
        epic = Epic(
            slug="authentication",
            description="Authentication features",
            story_refs=["User Login"],
        )
        await epic_repo.save(epic)

        # Execute
        request = StoryOrchestrationRequest(story=sample_story)
        response = await use_case.execute(request)

        # Verify: No conditions detected
        assert len(response.conditions) == 0
        assert not response.has_unknown_persona
        assert not response.has_orphan_story

    @pytest.mark.asyncio
    async def test_unknown_persona_condition(
        self,
        use_case: StoryOrchestrationUseCase,
        epic_repo: MemoryEpicRepository,
        sample_story: Story,
    ) -> None:
        """Test unknown persona condition is detected when persona not in repo."""
        # Setup: Epic containing story (so we only get unknown persona condition)
        epic = Epic(
            slug="authentication",
            description="Authentication features",
            story_refs=["User Login"],
        )
        await epic_repo.save(epic)

        # Execute (no personas in repo)
        request = StoryOrchestrationRequest(story=sample_story)
        response = await use_case.execute(request)

        # Verify: Unknown persona detected
        assert len(response.conditions) == 1
        assert response.has_unknown_persona
        assert not response.has_orphan_story

        condition = response.conditions[0]
        assert condition.condition == "unknown_persona"
        assert condition.story_slug == sample_story.slug
        assert condition.details["persona_name"] == "Customer"

    @pytest.mark.asyncio
    async def test_orphan_story_condition(
        self,
        use_case: StoryOrchestrationUseCase,
        persona_repo: MemoryPersonaRepository,
        sample_story: Story,
    ) -> None:
        """Test orphan story condition is detected when story not in any epic."""
        # Setup: Known persona (so we only get orphan condition)
        persona = Persona.from_story_reference("Customer")
        await persona_repo.save(persona)

        # Execute (no epics in repo)
        request = StoryOrchestrationRequest(story=sample_story)
        response = await use_case.execute(request)

        # Verify: Orphan story detected
        assert len(response.conditions) == 1
        assert not response.has_unknown_persona
        assert response.has_orphan_story

        condition = response.conditions[0]
        assert condition.condition == "orphan_story"
        assert condition.story_slug == sample_story.slug
        assert condition.details["feature_title"] == "User Login"

    @pytest.mark.asyncio
    async def test_both_conditions_detected(
        self,
        use_case: StoryOrchestrationUseCase,
        sample_story: Story,
    ) -> None:
        """Test both conditions are detected when applicable."""
        # Execute (empty repos - both conditions apply)
        request = StoryOrchestrationRequest(story=sample_story)
        response = await use_case.execute(request)

        # Verify: Both conditions detected
        assert len(response.conditions) == 2
        assert response.has_unknown_persona
        assert response.has_orphan_story

        condition_types = {c.condition for c in response.conditions}
        assert "unknown_persona" in condition_types
        assert "orphan_story" in condition_types

    @pytest.mark.asyncio
    async def test_unknown_persona_not_detected_for_unknown_persona_name(
        self,
        use_case: StoryOrchestrationUseCase,
        epic_repo: MemoryEpicRepository,
    ) -> None:
        """Test unknown persona condition skipped when persona is literally 'unknown'."""
        # Story with persona="unknown"
        story = Story.from_feature_file(
            feature_title="System Task",
            persona="unknown",
            i_want="process data",
            so_that="the system works",
            app_slug="backend",
            file_path="features/task.feature",
        )

        # Setup: Epic containing story
        epic = Epic(
            slug="backend-tasks",
            description="Backend tasks",
            story_refs=["System Task"],
        )
        await epic_repo.save(epic)

        # Execute
        request = StoryOrchestrationRequest(story=story)
        response = await use_case.execute(request)

        # Verify: No unknown persona condition (persona="unknown" is intentional)
        assert not response.has_unknown_persona
        assert len(response.conditions) == 0

    @pytest.mark.asyncio
    async def test_story_in_epic_with_different_title_is_orphan(
        self,
        use_case: StoryOrchestrationUseCase,
        persona_repo: MemoryPersonaRepository,
        epic_repo: MemoryEpicRepository,
        sample_story: Story,
    ) -> None:
        """Test story is orphan when epic has different story refs."""
        # Setup: Known persona
        persona = Persona.from_story_reference("Customer")
        await persona_repo.save(persona)

        # Setup: Epic with different stories
        epic = Epic(
            slug="other-epic",
            description="Other features",
            story_refs=["Different Story", "Another Story"],
        )
        await epic_repo.save(epic)

        # Execute
        request = StoryOrchestrationRequest(story=sample_story)
        response = await use_case.execute(request)

        # Verify: Orphan story detected
        assert response.has_orphan_story

    @pytest.mark.asyncio
    async def test_response_contains_original_story(
        self,
        use_case: StoryOrchestrationUseCase,
        sample_story: Story,
    ) -> None:
        """Test response contains the original story."""
        request = StoryOrchestrationRequest(story=sample_story)
        response = await use_case.execute(request)

        assert response.story == sample_story
