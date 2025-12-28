"""Tests for HCD handlers.

Tests for fine-grained and coarse-grained handlers:
- Story handlers: NullOrphanStoryHandler, LoggingOrphanStoryHandler, etc.
- Epic handlers: NullEmptyEpicHandler, LoggingEmptyEpicHandler, etc.
- Journey handlers: NullEmptyJourneyHandler, LoggingEmptyJourneyHandler, etc.

Handler tests verify:
- Fine-grained handlers produce correct acknowledgements
- Coarse-grained handlers delegate to their internal use cases

Business logic (condition detection) is tested in the respective use case tests.
"""

from unittest.mock import AsyncMock

import pytest

from julee.core.entities.acknowledgement import Acknowledgement
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.journey import Journey, JourneyStep
from julee.hcd.entities.story import Story
from julee.hcd.infrastructure.handlers.epic_orchestration import (
    EpicOrchestrationHandler,
)
from julee.hcd.infrastructure.handlers.journey_orchestration import (
    JourneyOrchestrationHandler,
)
from julee.hcd.infrastructure.handlers.null_handlers import (
    LoggingEmptyEpicHandler,
    LoggingEmptyJourneyHandler,
    LoggingOrphanStoryHandler,
    LoggingUnknownJourneyEpicRefHandler,
    LoggingUnknownJourneyPersonaHandler,
    LoggingUnknownJourneyStoryRefHandler,
    LoggingUnknownPersonaHandler,
    LoggingUnknownStoryRefHandler,
    NullEmptyEpicHandler,
    NullEmptyJourneyHandler,
    NullOrphanStoryHandler,
    NullStoryCreatedHandler,
    NullUnknownJourneyEpicRefHandler,
    NullUnknownJourneyPersonaHandler,
    NullUnknownJourneyStoryRefHandler,
    NullUnknownPersonaHandler,
    NullUnknownStoryRefHandler,
)
from julee.hcd.infrastructure.handlers.story_orchestration import (
    StoryOrchestrationHandler,
)
from julee.hcd.use_cases.epic_orchestration import EpicOrchestrationResponse
from julee.hcd.use_cases.journey_orchestration import JourneyOrchestrationResponse
from julee.hcd.use_cases.story_orchestration import StoryOrchestrationResponse


class TestNullHandlers:
    """Test null handler implementations.

    Null handlers acknowledge without action, used for testing.
    """

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
    async def test_null_orphan_handler_acknowledges(self, sample_story: Story) -> None:
        """Test NullOrphanStoryHandler acknowledges without action."""
        handler = NullOrphanStoryHandler()

        ack = await handler.handle(sample_story)

        assert isinstance(ack, Acknowledgement)
        assert ack.will_comply is True
        assert ack.errors == []

    @pytest.mark.asyncio
    async def test_null_unknown_persona_handler_acknowledges(
        self, sample_story: Story
    ) -> None:
        """Test NullUnknownPersonaHandler acknowledges without action."""
        handler = NullUnknownPersonaHandler()

        ack = await handler.handle(sample_story, "Unknown Persona")

        assert isinstance(ack, Acknowledgement)
        assert ack.will_comply is True
        assert ack.errors == []

    @pytest.mark.asyncio
    async def test_null_story_created_handler_acknowledges(
        self, sample_story: Story
    ) -> None:
        """Test NullStoryCreatedHandler acknowledges without action."""
        handler = NullStoryCreatedHandler()

        ack = await handler.handle(sample_story)

        assert isinstance(ack, Acknowledgement)
        assert ack.will_comply is True
        assert ack.errors == []


class TestLoggingHandlers:
    """Test logging handler implementations.

    Fine-grained handlers that log conditions without business logic.
    """

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
    async def test_logging_orphan_handler_acknowledges_with_warning(
        self, sample_story: Story
    ) -> None:
        """Test LoggingOrphanStoryHandler acknowledges with warning."""
        handler = LoggingOrphanStoryHandler()

        ack = await handler.handle(sample_story)

        assert isinstance(ack, Acknowledgement)
        assert ack.will_comply is True
        assert len(ack.warnings) == 1
        assert "User Login" in ack.warnings[0]
        assert "not in any epic" in ack.warnings[0]

    @pytest.mark.asyncio
    async def test_logging_unknown_persona_handler_acknowledges_with_warning(
        self, sample_story: Story
    ) -> None:
        """Test LoggingUnknownPersonaHandler acknowledges with warning."""
        handler = LoggingUnknownPersonaHandler()

        ack = await handler.handle(sample_story, "Mystery User")

        assert isinstance(ack, Acknowledgement)
        assert ack.will_comply is True
        assert len(ack.warnings) == 1
        assert "Mystery User" in ack.warnings[0]
        assert "not defined" in ack.warnings[0]


class TestStoryOrchestrationHandler:
    """Test coarse-grained story orchestration handler.

    Only tests that handler calls its internal use case.
    Business logic is tested in test_story_orchestration.py.
    """

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
    async def test_handler_calls_internal_use_case(
        self,
        sample_story: Story,
    ) -> None:
        """Test handler calls its internal use case with the story."""
        # Setup: Mock use case
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = StoryOrchestrationResponse(
            story=sample_story, conditions=[]
        )

        # Setup: Handler with mock use case and real fine-grained handlers
        handler = StoryOrchestrationHandler(
            orchestration_use_case=mock_use_case,
            orphan_handler=NullOrphanStoryHandler(),
            unknown_persona_handler=NullUnknownPersonaHandler(),
        )

        # Execute
        await handler.handle(sample_story)

        # Verify: Use case was called with correct request
        mock_use_case.execute.assert_called_once()
        request = mock_use_case.execute.call_args[0][0]
        assert request.story == sample_story


# =============================================================================
# Epic Handler Tests
# =============================================================================


class TestEpicNullHandlers:
    """Test Epic null handler implementations."""

    @pytest.fixture
    def sample_epic(self) -> Epic:
        """Create a sample epic for testing."""
        return Epic(
            slug="authentication",
            description="Auth features",
            story_refs=["User Login"],
        )

    @pytest.mark.asyncio
    async def test_null_empty_epic_handler_acknowledges(
        self, sample_epic: Epic
    ) -> None:
        """Test NullEmptyEpicHandler acknowledges without action."""
        handler = NullEmptyEpicHandler()
        ack = await handler.handle(sample_epic)
        assert ack.will_comply is True

    @pytest.mark.asyncio
    async def test_null_unknown_story_ref_handler_acknowledges(
        self, sample_epic: Epic
    ) -> None:
        """Test NullUnknownStoryRefHandler acknowledges without action."""
        handler = NullUnknownStoryRefHandler()
        ack = await handler.handle(sample_epic, ["Unknown Story"])
        assert ack.will_comply is True


class TestEpicLoggingHandlers:
    """Test Epic logging handler implementations."""

    @pytest.fixture
    def sample_epic(self) -> Epic:
        """Create a sample epic for testing."""
        return Epic(
            slug="authentication",
            description="Auth features",
            story_refs=["User Login"],
        )

    @pytest.mark.asyncio
    async def test_logging_empty_epic_handler(self, sample_epic: Epic) -> None:
        """Test LoggingEmptyEpicHandler acknowledges with warning."""
        handler = LoggingEmptyEpicHandler()
        ack = await handler.handle(sample_epic)
        assert ack.will_comply is True
        assert len(ack.warnings) == 1
        assert "authentication" in ack.warnings[0]

    @pytest.mark.asyncio
    async def test_logging_unknown_story_ref_handler(self, sample_epic: Epic) -> None:
        """Test LoggingUnknownStoryRefHandler acknowledges with warning."""
        handler = LoggingUnknownStoryRefHandler()
        ack = await handler.handle(sample_epic, ["Unknown Story", "Another"])
        assert ack.will_comply is True
        assert len(ack.warnings) == 1
        assert "Unknown Story" in ack.warnings[0]


class TestEpicOrchestrationHandler:
    """Test coarse-grained epic orchestration handler."""

    @pytest.fixture
    def sample_epic(self) -> Epic:
        """Create a sample epic for testing."""
        return Epic(
            slug="authentication",
            description="Auth features",
            story_refs=["User Login"],
        )

    @pytest.mark.asyncio
    async def test_handler_calls_internal_use_case(self, sample_epic: Epic) -> None:
        """Test handler calls its internal use case with the epic."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = EpicOrchestrationResponse(
            epic=sample_epic, conditions=[]
        )

        handler = EpicOrchestrationHandler(
            orchestration_use_case=mock_use_case,
            empty_epic_handler=NullEmptyEpicHandler(),
            unknown_story_ref_handler=NullUnknownStoryRefHandler(),
        )

        await handler.handle(sample_epic)

        mock_use_case.execute.assert_called_once()
        request = mock_use_case.execute.call_args[0][0]
        assert request.epic == sample_epic


# =============================================================================
# Journey Handler Tests
# =============================================================================


class TestJourneyNullHandlers:
    """Test Journey null handler implementations."""

    @pytest.fixture
    def sample_journey(self) -> Journey:
        """Create a sample journey for testing."""
        return Journey(
            slug="onboarding",
            persona="Customer",
            intent="Get started",
            outcome="Ready to use",
            steps=[JourneyStep.story("User Registration")],
        )

    @pytest.mark.asyncio
    async def test_null_empty_journey_handler_acknowledges(
        self, sample_journey: Journey
    ) -> None:
        """Test NullEmptyJourneyHandler acknowledges without action."""
        handler = NullEmptyJourneyHandler()
        ack = await handler.handle(sample_journey)
        assert ack.will_comply is True

    @pytest.mark.asyncio
    async def test_null_unknown_journey_persona_handler_acknowledges(
        self, sample_journey: Journey
    ) -> None:
        """Test NullUnknownJourneyPersonaHandler acknowledges without action."""
        handler = NullUnknownJourneyPersonaHandler()
        ack = await handler.handle(sample_journey, "Unknown Persona")
        assert ack.will_comply is True

    @pytest.mark.asyncio
    async def test_null_unknown_journey_story_ref_handler_acknowledges(
        self, sample_journey: Journey
    ) -> None:
        """Test NullUnknownJourneyStoryRefHandler acknowledges without action."""
        handler = NullUnknownJourneyStoryRefHandler()
        ack = await handler.handle(sample_journey, ["Unknown Story"])
        assert ack.will_comply is True

    @pytest.mark.asyncio
    async def test_null_unknown_journey_epic_ref_handler_acknowledges(
        self, sample_journey: Journey
    ) -> None:
        """Test NullUnknownJourneyEpicRefHandler acknowledges without action."""
        handler = NullUnknownJourneyEpicRefHandler()
        ack = await handler.handle(sample_journey, ["unknown-epic"])
        assert ack.will_comply is True


class TestJourneyLoggingHandlers:
    """Test Journey logging handler implementations."""

    @pytest.fixture
    def sample_journey(self) -> Journey:
        """Create a sample journey for testing."""
        return Journey(
            slug="onboarding",
            persona="Customer",
            intent="Get started",
            outcome="Ready to use",
            steps=[JourneyStep.story("User Registration")],
        )

    @pytest.mark.asyncio
    async def test_logging_empty_journey_handler(self, sample_journey: Journey) -> None:
        """Test LoggingEmptyJourneyHandler acknowledges with warning."""
        handler = LoggingEmptyJourneyHandler()
        ack = await handler.handle(sample_journey)
        assert ack.will_comply is True
        assert len(ack.warnings) == 1
        assert "onboarding" in ack.warnings[0]

    @pytest.mark.asyncio
    async def test_logging_unknown_journey_persona_handler(
        self, sample_journey: Journey
    ) -> None:
        """Test LoggingUnknownJourneyPersonaHandler acknowledges with warning."""
        handler = LoggingUnknownJourneyPersonaHandler()
        ack = await handler.handle(sample_journey, "Mystery Persona")
        assert ack.will_comply is True
        assert len(ack.warnings) == 1
        assert "Mystery Persona" in ack.warnings[0]

    @pytest.mark.asyncio
    async def test_logging_unknown_journey_story_ref_handler(
        self, sample_journey: Journey
    ) -> None:
        """Test LoggingUnknownJourneyStoryRefHandler acknowledges with warning."""
        handler = LoggingUnknownJourneyStoryRefHandler()
        ack = await handler.handle(sample_journey, ["Unknown Story"])
        assert ack.will_comply is True
        assert len(ack.warnings) == 1
        assert "Unknown Story" in ack.warnings[0]

    @pytest.mark.asyncio
    async def test_logging_unknown_journey_epic_ref_handler(
        self, sample_journey: Journey
    ) -> None:
        """Test LoggingUnknownJourneyEpicRefHandler acknowledges with warning."""
        handler = LoggingUnknownJourneyEpicRefHandler()
        ack = await handler.handle(sample_journey, ["unknown-epic"])
        assert ack.will_comply is True
        assert len(ack.warnings) == 1
        assert "unknown-epic" in ack.warnings[0]


class TestJourneyOrchestrationHandler:
    """Test coarse-grained journey orchestration handler."""

    @pytest.fixture
    def sample_journey(self) -> Journey:
        """Create a sample journey for testing."""
        return Journey(
            slug="onboarding",
            persona="Customer",
            intent="Get started",
            outcome="Ready to use",
            steps=[JourneyStep.story("User Registration")],
        )

    @pytest.mark.asyncio
    async def test_handler_calls_internal_use_case(
        self, sample_journey: Journey
    ) -> None:
        """Test handler calls its internal use case with the journey."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = JourneyOrchestrationResponse(
            journey=sample_journey, conditions=[]
        )

        handler = JourneyOrchestrationHandler(
            orchestration_use_case=mock_use_case,
            unknown_persona_handler=NullUnknownJourneyPersonaHandler(),
            unknown_story_ref_handler=NullUnknownJourneyStoryRefHandler(),
            unknown_epic_ref_handler=NullUnknownJourneyEpicRefHandler(),
            empty_journey_handler=NullEmptyJourneyHandler(),
        )

        await handler.handle(sample_journey)

        mock_use_case.execute.assert_called_once()
        request = mock_use_case.execute.call_args[0][0]
        assert request.journey == sample_journey
