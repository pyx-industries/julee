"""Tests for story handlers.

Tests for fine-grained and coarse-grained handlers:
- NullOrphanStoryHandler, NullUnknownPersonaHandler, NullStoryCreatedHandler
- LoggingOrphanStoryHandler, LoggingUnknownPersonaHandler
- StoryOrchestrationHandler (coarse-grained)

Handler tests verify:
- Fine-grained handlers produce correct acknowledgements
- Coarse-grained handler delegates to use case and fine-grained handlers
- Handler aggregates acknowledgements from delegates

Business logic (condition detection) is tested in test_story_orchestration.py.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from julee.core.entities.acknowledgement import Acknowledgement
from julee.hcd.entities.story import Story
from julee.hcd.infrastructure.handlers.null_handlers import (
    LoggingOrphanStoryHandler,
    LoggingUnknownPersonaHandler,
    NullOrphanStoryHandler,
    NullStoryCreatedHandler,
    NullUnknownPersonaHandler,
)
from julee.hcd.infrastructure.handlers.story_orchestration import (
    StoryOrchestrationHandler,
)
from julee.hcd.use_cases.story_orchestration import (
    StoryCondition,
    StoryOrchestrationResponse,
)


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
    async def test_null_orphan_handler_acknowledges(
        self, sample_story: Story
    ) -> None:
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
