"""Tests for Journey CRUD use cases."""

import pytest

from julee.docs.hcd_api.requests import (
    CreateJourneyRequest,
    DeleteJourneyRequest,
    GetJourneyRequest,
    JourneyStepInput,
    ListJourneysRequest,
    UpdateJourneyRequest,
)
from julee.docs.sphinx_hcd.domain.models.journey import Journey, JourneyStep, StepType
from julee.docs.sphinx_hcd.domain.use_cases.journey import (
    CreateJourneyUseCase,
    DeleteJourneyUseCase,
    GetJourneyUseCase,
    ListJourneysUseCase,
    UpdateJourneyUseCase,
)
from julee.docs.sphinx_hcd.repositories.memory.journey import MemoryJourneyRepository


class TestCreateJourneyUseCase:
    """Test creating journeys."""

    @pytest.fixture
    def repo(self) -> MemoryJourneyRepository:
        """Create a fresh repository."""
        return MemoryJourneyRepository()

    @pytest.fixture
    def use_case(self, repo: MemoryJourneyRepository) -> CreateJourneyUseCase:
        """Create the use case with repository."""
        return CreateJourneyUseCase(repo)

    @pytest.mark.asyncio
    async def test_create_journey_success(
        self,
        use_case: CreateJourneyUseCase,
        repo: MemoryJourneyRepository,
    ) -> None:
        """Test successfully creating a journey."""
        request = CreateJourneyRequest(
            slug="new-employee-onboarding",
            persona="New Employee",
            intent="Get set up in my new role",
            outcome="Fully productive team member",
            goal="Complete onboarding process",
            depends_on=["hr-approval"],
            steps=[
                JourneyStepInput(
                    step_type="story",
                    ref="receive-welcome-email",
                    description="Get welcome email",
                ),
                JourneyStepInput(
                    step_type="story",
                    ref="complete-training",
                    description="Finish training modules",
                ),
            ],
        )

        response = await use_case.execute(request)

        assert response.journey is not None
        assert response.journey.slug == "new-employee-onboarding"
        assert response.journey.persona == "New Employee"
        assert response.journey.intent == "Get set up in my new role"
        assert len(response.journey.steps) == 2

        # Verify it's persisted
        stored = await repo.get("new-employee-onboarding")
        assert stored is not None

    @pytest.mark.asyncio
    async def test_create_journey_with_defaults(
        self, use_case: CreateJourneyUseCase
    ) -> None:
        """Test creating journey with default values."""
        request = CreateJourneyRequest(slug="minimal-journey")

        response = await use_case.execute(request)

        assert response.journey.persona == ""
        assert response.journey.intent == ""
        assert response.journey.outcome == ""
        assert response.journey.goal == ""
        assert response.journey.depends_on == []
        assert response.journey.steps == []

    @pytest.mark.asyncio
    async def test_create_journey_with_preconditions(
        self, use_case: CreateJourneyUseCase
    ) -> None:
        """Test creating journey with preconditions and postconditions."""
        request = CreateJourneyRequest(
            slug="guarded-journey",
            persona="User",
            preconditions=["Must be logged in", "Must have permissions"],
            postconditions=["Data is saved", "User notified"],
        )

        response = await use_case.execute(request)

        assert response.journey.preconditions == [
            "Must be logged in",
            "Must have permissions",
        ]
        assert response.journey.postconditions == [
            "Data is saved",
            "User notified",
        ]


class TestGetJourneyUseCase:
    """Test getting journeys."""

    @pytest.fixture
    def repo(self) -> MemoryJourneyRepository:
        """Create a fresh repository."""
        return MemoryJourneyRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryJourneyRepository
    ) -> MemoryJourneyRepository:
        """Create repository with sample data."""
        await repo.save(
            Journey(
                slug="test-journey",
                persona="Tester",
                intent="Verify functionality",
                outcome="High quality software",
                goal="Complete testing",
            )
        )
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryJourneyRepository) -> GetJourneyUseCase:
        """Create the use case with populated repository."""
        return GetJourneyUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_get_existing_journey(self, use_case: GetJourneyUseCase) -> None:
        """Test getting an existing journey."""
        request = GetJourneyRequest(slug="test-journey")

        response = await use_case.execute(request)

        assert response.journey is not None
        assert response.journey.slug == "test-journey"
        assert response.journey.persona == "Tester"

    @pytest.mark.asyncio
    async def test_get_nonexistent_journey(self, use_case: GetJourneyUseCase) -> None:
        """Test getting a nonexistent journey returns None."""
        request = GetJourneyRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.journey is None


class TestListJourneysUseCase:
    """Test listing journeys."""

    @pytest.fixture
    def repo(self) -> MemoryJourneyRepository:
        """Create a fresh repository."""
        return MemoryJourneyRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryJourneyRepository
    ) -> MemoryJourneyRepository:
        """Create repository with sample data."""
        journeys = [
            Journey(slug="journey-1", persona="User A"),
            Journey(slug="journey-2", persona="User B"),
            Journey(slug="journey-3", persona="User C"),
        ]
        for journey in journeys:
            await repo.save(journey)
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryJourneyRepository) -> ListJourneysUseCase:
        """Create the use case with populated repository."""
        return ListJourneysUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_list_all_journeys(self, use_case: ListJourneysUseCase) -> None:
        """Test listing all journeys."""
        request = ListJourneysRequest()

        response = await use_case.execute(request)

        assert len(response.journeys) == 3
        slugs = {j.slug for j in response.journeys}
        assert slugs == {"journey-1", "journey-2", "journey-3"}

    @pytest.mark.asyncio
    async def test_list_empty_repo(self, repo: MemoryJourneyRepository) -> None:
        """Test listing returns empty list when no journeys."""
        use_case = ListJourneysUseCase(repo)
        request = ListJourneysRequest()

        response = await use_case.execute(request)

        assert response.journeys == []


class TestUpdateJourneyUseCase:
    """Test updating journeys."""

    @pytest.fixture
    def repo(self) -> MemoryJourneyRepository:
        """Create a fresh repository."""
        return MemoryJourneyRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryJourneyRepository
    ) -> MemoryJourneyRepository:
        """Create repository with sample data."""
        await repo.save(
            Journey(
                slug="update-journey",
                persona="Original Persona",
                intent="Original intent",
                outcome="Original outcome",
                goal="Original goal",
                steps=[
                    JourneyStep(
                        step_type=StepType.STORY,
                        ref="original-step",
                    )
                ],
            )
        )
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryJourneyRepository) -> UpdateJourneyUseCase:
        """Create the use case with populated repository."""
        return UpdateJourneyUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_update_single_field(self, use_case: UpdateJourneyUseCase) -> None:
        """Test updating a single field."""
        request = UpdateJourneyRequest(
            slug="update-journey",
            intent="Updated intent",
        )

        response = await use_case.execute(request)

        assert response.journey is not None
        assert response.found is True
        assert response.journey.intent == "Updated intent"
        # Other fields unchanged
        assert response.journey.persona == "Original Persona"
        assert response.journey.outcome == "Original outcome"

    @pytest.mark.asyncio
    async def test_update_steps(self, use_case: UpdateJourneyUseCase) -> None:
        """Test updating steps."""
        request = UpdateJourneyRequest(
            slug="update-journey",
            steps=[
                JourneyStepInput(
                    step_type="story",
                    ref="new-step-1",
                    description="First new step",
                ),
                JourneyStepInput(
                    step_type="story",
                    ref="new-step-2",
                    description="Second new step",
                ),
            ],
        )

        response = await use_case.execute(request)

        assert len(response.journey.steps) == 2
        assert response.journey.steps[0].ref == "new-step-1"
        assert response.journey.steps[1].ref == "new-step-2"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, use_case: UpdateJourneyUseCase) -> None:
        """Test updating multiple fields."""
        request = UpdateJourneyRequest(
            slug="update-journey",
            persona="New Persona",
            goal="New goal",
            depends_on=["prerequisite-journey"],
        )

        response = await use_case.execute(request)

        assert response.journey.persona == "New Persona"
        assert response.journey.goal == "New goal"
        assert response.journey.depends_on == ["prerequisite-journey"]

    @pytest.mark.asyncio
    async def test_update_nonexistent_journey(
        self, use_case: UpdateJourneyUseCase
    ) -> None:
        """Test updating nonexistent journey returns None."""
        request = UpdateJourneyRequest(
            slug="nonexistent",
            intent="New intent",
        )

        response = await use_case.execute(request)

        assert response.journey is None
        assert response.found is False


class TestDeleteJourneyUseCase:
    """Test deleting journeys."""

    @pytest.fixture
    def repo(self) -> MemoryJourneyRepository:
        """Create a fresh repository."""
        return MemoryJourneyRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryJourneyRepository
    ) -> MemoryJourneyRepository:
        """Create repository with sample data."""
        await repo.save(Journey(slug="to-delete", persona="To Delete"))
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryJourneyRepository) -> DeleteJourneyUseCase:
        """Create the use case with populated repository."""
        return DeleteJourneyUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_delete_existing_journey(
        self,
        use_case: DeleteJourneyUseCase,
        populated_repo: MemoryJourneyRepository,
    ) -> None:
        """Test successfully deleting a journey."""
        request = DeleteJourneyRequest(slug="to-delete")

        response = await use_case.execute(request)

        assert response.deleted is True

        # Verify it's removed
        stored = await populated_repo.get("to-delete")
        assert stored is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_journey(
        self, use_case: DeleteJourneyUseCase
    ) -> None:
        """Test deleting nonexistent journey returns False."""
        request = DeleteJourneyRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.deleted is False
