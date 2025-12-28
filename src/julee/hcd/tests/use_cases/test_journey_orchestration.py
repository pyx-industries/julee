"""Tests for JourneyOrchestrationUseCase.

Tests the business logic for detecting journey orchestration conditions:
- Unknown persona (persona not found in PersonaRepository)
- Unknown story refs (story steps not found in StoryRepository)
- Unknown epic refs (epic steps not found in EpicRepository)
- Empty journey (no steps)
"""

import pytest

from julee.hcd.entities.epic import Epic
from julee.hcd.entities.journey import Journey, JourneyStep
from julee.hcd.entities.persona import Persona
from julee.hcd.entities.story import Story
from julee.hcd.infrastructure.repositories.memory.epic import MemoryEpicRepository
from julee.hcd.infrastructure.repositories.memory.persona import MemoryPersonaRepository
from julee.hcd.infrastructure.repositories.memory.story import MemoryStoryRepository
from julee.hcd.use_cases.journey_orchestration import (
    JourneyOrchestrationRequest,
    JourneyOrchestrationUseCase,
)


class TestJourneyOrchestrationUseCase:
    """Test journey orchestration condition detection."""

    @pytest.fixture
    def persona_repo(self) -> MemoryPersonaRepository:
        """Create fresh persona repository."""
        return MemoryPersonaRepository()

    @pytest.fixture
    def story_repo(self) -> MemoryStoryRepository:
        """Create fresh story repository."""
        return MemoryStoryRepository()

    @pytest.fixture
    def epic_repo(self) -> MemoryEpicRepository:
        """Create fresh epic repository."""
        return MemoryEpicRepository()

    @pytest.fixture
    def use_case(
        self,
        persona_repo: MemoryPersonaRepository,
        story_repo: MemoryStoryRepository,
        epic_repo: MemoryEpicRepository,
    ) -> JourneyOrchestrationUseCase:
        """Create use case with repositories."""
        return JourneyOrchestrationUseCase(
            persona_repo=persona_repo,
            story_repo=story_repo,
            epic_repo=epic_repo,
        )

    @pytest.fixture
    def sample_journey(self) -> Journey:
        """Create a sample journey with steps."""
        return Journey(
            slug="user-onboarding",
            persona="Customer",
            intent="Get started with the platform",
            outcome="Account is set up and ready to use",
            steps=[
                JourneyStep.story("User Registration"),
                JourneyStep.epic("authentication"),
                JourneyStep.phase("Complete Setup"),
            ],
        )

    @pytest.fixture
    def empty_journey(self) -> Journey:
        """Create an empty journey (no steps)."""
        return Journey(
            slug="empty-journey",
            persona="Customer",
            intent="Something",
            outcome="Something else",
            steps=[],
        )

    @pytest.mark.asyncio
    async def test_no_conditions_when_all_refs_exist(
        self,
        use_case: JourneyOrchestrationUseCase,
        persona_repo: MemoryPersonaRepository,
        story_repo: MemoryStoryRepository,
        epic_repo: MemoryEpicRepository,
        sample_journey: Journey,
    ) -> None:
        """Test no conditions when persona, stories, and epics all exist."""
        # Setup: Known persona
        persona = Persona.from_story_reference("Customer")
        await persona_repo.save(persona)

        # Setup: Known story
        story = Story.from_feature_file(
            feature_title="User Registration",
            persona="Customer",
            i_want="register",
            so_that="use the platform",
            app_slug="app",
            file_path="features/registration.feature",
        )
        await story_repo.save(story)

        # Setup: Known epic
        epic = Epic(slug="authentication", description="Auth features")
        await epic_repo.save(epic)

        # Execute
        request = JourneyOrchestrationRequest(journey=sample_journey)
        response = await use_case.execute(request)

        # Verify: No conditions
        assert len(response.conditions) == 0
        assert not response.has_unknown_persona
        assert not response.has_unknown_story_refs
        assert not response.has_unknown_epic_refs
        assert not response.has_empty_journey

    @pytest.mark.asyncio
    async def test_unknown_persona_condition(
        self,
        use_case: JourneyOrchestrationUseCase,
        story_repo: MemoryStoryRepository,
        epic_repo: MemoryEpicRepository,
        sample_journey: Journey,
    ) -> None:
        """Test unknown persona condition when persona not in repo."""
        # Setup: Known story and epic (no persona)
        story = Story.from_feature_file(
            feature_title="User Registration",
            persona="Customer",
            i_want="register",
            so_that="use the platform",
            app_slug="app",
            file_path="features/registration.feature",
        )
        await story_repo.save(story)

        epic = Epic(slug="authentication", description="Auth features")
        await epic_repo.save(epic)

        # Execute
        request = JourneyOrchestrationRequest(journey=sample_journey)
        response = await use_case.execute(request)

        # Verify: Unknown persona detected
        assert response.has_unknown_persona
        condition = next(c for c in response.conditions if c.condition == "unknown_persona")
        assert condition.journey_slug == "user-onboarding"
        assert condition.details["persona_name"] == "Customer"

    @pytest.mark.asyncio
    async def test_empty_journey_condition(
        self,
        use_case: JourneyOrchestrationUseCase,
        persona_repo: MemoryPersonaRepository,
        empty_journey: Journey,
    ) -> None:
        """Test empty journey condition when no steps."""
        # Setup: Known persona
        persona = Persona.from_story_reference("Customer")
        await persona_repo.save(persona)

        # Execute
        request = JourneyOrchestrationRequest(journey=empty_journey)
        response = await use_case.execute(request)

        # Verify: Empty journey detected
        assert response.has_empty_journey
        condition = next(c for c in response.conditions if c.condition == "empty_journey")
        assert condition.journey_slug == "empty-journey"

    @pytest.mark.asyncio
    async def test_unknown_story_refs_condition(
        self,
        use_case: JourneyOrchestrationUseCase,
        persona_repo: MemoryPersonaRepository,
        epic_repo: MemoryEpicRepository,
        sample_journey: Journey,
    ) -> None:
        """Test unknown story refs when story steps don't exist."""
        # Setup: Known persona and epic (no stories)
        persona = Persona.from_story_reference("Customer")
        await persona_repo.save(persona)

        epic = Epic(slug="authentication", description="Auth features")
        await epic_repo.save(epic)

        # Execute
        request = JourneyOrchestrationRequest(journey=sample_journey)
        response = await use_case.execute(request)

        # Verify: Unknown story refs detected
        assert response.has_unknown_story_refs
        condition = next(c for c in response.conditions if c.condition == "unknown_story_refs")
        assert condition.details["unknown_refs"] == ["User Registration"]

    @pytest.mark.asyncio
    async def test_unknown_epic_refs_condition(
        self,
        use_case: JourneyOrchestrationUseCase,
        persona_repo: MemoryPersonaRepository,
        story_repo: MemoryStoryRepository,
        sample_journey: Journey,
    ) -> None:
        """Test unknown epic refs when epic steps don't exist."""
        # Setup: Known persona and story (no epics)
        persona = Persona.from_story_reference("Customer")
        await persona_repo.save(persona)

        story = Story.from_feature_file(
            feature_title="User Registration",
            persona="Customer",
            i_want="register",
            so_that="use the platform",
            app_slug="app",
            file_path="features/registration.feature",
        )
        await story_repo.save(story)

        # Execute
        request = JourneyOrchestrationRequest(journey=sample_journey)
        response = await use_case.execute(request)

        # Verify: Unknown epic refs detected
        assert response.has_unknown_epic_refs
        condition = next(c for c in response.conditions if c.condition == "unknown_epic_refs")
        assert condition.details["unknown_refs"] == ["authentication"]

    @pytest.mark.asyncio
    async def test_multiple_conditions_detected(
        self,
        use_case: JourneyOrchestrationUseCase,
        sample_journey: Journey,
    ) -> None:
        """Test multiple conditions are detected when applicable."""
        # Execute (empty repos - multiple conditions apply)
        request = JourneyOrchestrationRequest(journey=sample_journey)
        response = await use_case.execute(request)

        # Verify: Multiple conditions
        assert response.has_unknown_persona
        assert response.has_unknown_story_refs
        assert response.has_unknown_epic_refs

    @pytest.mark.asyncio
    async def test_unknown_persona_skipped_for_literal_unknown(
        self,
        use_case: JourneyOrchestrationUseCase,
    ) -> None:
        """Test unknown persona condition skipped when persona is 'unknown'."""
        journey = Journey(
            slug="system-journey",
            persona="unknown",
            intent="System process",
            outcome="Done",
            steps=[JourneyStep.phase("Do things")],
        )

        # Execute
        request = JourneyOrchestrationRequest(journey=journey)
        response = await use_case.execute(request)

        # Verify: No unknown persona condition
        assert not response.has_unknown_persona

    @pytest.mark.asyncio
    async def test_response_contains_original_journey(
        self,
        use_case: JourneyOrchestrationUseCase,
        sample_journey: Journey,
    ) -> None:
        """Test response contains the original journey."""
        request = JourneyOrchestrationRequest(journey=sample_journey)
        response = await use_case.execute(request)

        assert response.journey == sample_journey
