"""Tests for HCDContext."""

import pytest

from apps.sphinx.hcd.context import (
    HCDContext,
    ensure_hcd_context,
    get_hcd_context,
    set_hcd_context,
)
from julee.supply_chain.entities.accelerator import Accelerator
from julee.hcd.entities.app import App, AppType
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.journey import Journey
from julee.hcd.entities.story import Story


class MockSphinxEnv:
    """Mock Sphinx environment for testing."""

    def __init__(self):
        self.hcd_storage = {}


class MockSphinxApp:
    """Mock Sphinx app for testing."""

    def __init__(self):
        self.env = MockSphinxEnv()


class TestHCDContextCreation:
    """Test HCDContext creation."""

    def test_create_context(self) -> None:
        """Test creating a new context."""
        context = HCDContext()

        assert context.story_repo is not None
        assert context.journey_repo is not None
        assert context.epic_repo is not None
        assert context.app_repo is not None
        assert context.accelerator_repo is not None
        assert context.integration_repo is not None
        assert context.code_info_repo is not None

    def test_repositories_are_independent(self) -> None:
        """Test that each context has its own repositories."""
        context1 = HCDContext()
        context2 = HCDContext()

        # Add to context1
        story = Story(
            slug="test-story",
            feature_title="Test Story",
            persona="Tester",
            i_want="test",
            so_that="verify",
            app_slug="test-app",
            file_path="test.feature",
        )
        context1.story_repo.save(story)

        # context2 should be empty
        assert context1.story_repo.get("test-story") is not None
        assert context2.story_repo.get("test-story") is None


class TestHCDContextOperations:
    """Test HCDContext operations."""

    @pytest.fixture
    def context(self) -> HCDContext:
        """Create a context with sample data."""
        ctx = HCDContext()

        # Add some entities
        ctx.story_repo.save(
            Story(
                slug="upload-document",
                feature_title="Upload Document",
                persona="Curator",
                i_want="upload",
                so_that="share",
                app_slug="vocab-tool",
                file_path="test.feature",
            )
        )

        ctx.journey_repo.save(
            Journey(
                slug="build-vocabulary",
                persona="Curator",
                docname="journeys/build-vocabulary",
            )
        )

        ctx.epic_repo.save(
            Epic(
                slug="vocabulary-management",
                description="Manage vocabularies",
                docname="epics/vocabulary-management",
            )
        )

        ctx.app_repo.save(
            App(
                slug="vocab-tool",
                name="Vocabulary Tool",
                app_type=AppType.STAFF,
                manifest_path="apps/vocab-tool/app.yaml",
            )
        )

        ctx.accelerator_repo.save(
            Accelerator(
                slug="vocabulary",
                status="alpha",
                docname="accelerators/vocabulary",
            )
        )

        return ctx

    def test_clear_all(self, context: HCDContext) -> None:
        """Test clearing all repositories."""
        # Verify data exists
        assert context.story_repo.get("upload-document") is not None
        assert context.journey_repo.get("build-vocabulary") is not None
        assert context.epic_repo.get("vocabulary-management") is not None
        assert context.app_repo.get("vocab-tool") is not None
        assert context.accelerator_repo.get("vocabulary") is not None

        # Clear all
        context.clear_all()

        # Verify all cleared
        assert context.story_repo.get("upload-document") is None
        assert context.journey_repo.get("build-vocabulary") is None
        assert context.epic_repo.get("vocabulary-management") is None
        assert context.app_repo.get("vocab-tool") is None
        assert context.accelerator_repo.get("vocabulary") is None

    def test_clear_by_docname(self, context: HCDContext) -> None:
        """Test clearing entities by docname."""
        # Add another journey with different docname
        context.journey_repo.save(
            Journey(
                slug="other-journey",
                persona="User",
                docname="journeys/other",
            )
        )

        # Clear by docname
        results = context.clear_by_docname("journeys/build-vocabulary")

        # Verify results
        assert results["journeys"] == 1
        assert results["epics"] == 0
        assert results["accelerators"] == 0

        # Verify correct entity cleared
        assert context.journey_repo.get("build-vocabulary") is None
        assert context.journey_repo.get("other-journey") is not None

    def test_clear_by_docname_multiple_types(self) -> None:
        """Test clearing entities across multiple types with same docname."""
        context = HCDContext()

        # Add entities with same docname
        context.journey_repo.save(
            Journey(
                slug="shared-journey",
                persona="User",
                docname="shared/doc",
            )
        )
        context.epic_repo.save(
            Epic(
                slug="shared-epic",
                docname="shared/doc",
            )
        )
        context.accelerator_repo.save(
            Accelerator(
                slug="shared-accel",
                docname="shared/doc",
            )
        )

        # Clear by docname
        results = context.clear_by_docname("shared/doc")

        # All should be cleared
        assert results["journeys"] == 1
        assert results["epics"] == 1
        assert results["accelerators"] == 1


class TestContextAccessFunctions:
    """Test context access helper functions."""

    def test_set_and_get_context(self) -> None:
        """Test setting and getting context from app."""
        app = MockSphinxApp()
        context = HCDContext()

        set_hcd_context(app, context)
        retrieved = get_hcd_context(app)

        assert retrieved is context

    def test_get_context_not_set(self) -> None:
        """Test getting context when not set raises error."""
        app = MockSphinxApp()

        with pytest.raises(AttributeError):
            get_hcd_context(app)

    def test_ensure_context_creates_new(self) -> None:
        """Test ensure_hcd_context creates new context if none exists."""
        app = MockSphinxApp()

        context = ensure_hcd_context(app)

        assert context is not None
        assert isinstance(context, HCDContext)

    def test_ensure_context_returns_existing(self) -> None:
        """Test ensure_hcd_context returns existing context."""
        app = MockSphinxApp()
        original = HCDContext()
        set_hcd_context(app, original)

        retrieved = ensure_hcd_context(app)

        assert retrieved is original

    def test_context_persists_on_app(self) -> None:
        """Test context persists on app object."""
        app = MockSphinxApp()
        context = HCDContext()

        # Add data through context
        context.story_repo.save(
            Story(
                slug="test",
                feature_title="Test",
                persona="User",
                i_want="test",
                so_that="verify",
                app_slug="app",
                file_path="test.feature",
            )
        )

        set_hcd_context(app, context)

        # Retrieve and verify data
        retrieved = get_hcd_context(app)
        assert retrieved.story_repo.get("test") is not None
