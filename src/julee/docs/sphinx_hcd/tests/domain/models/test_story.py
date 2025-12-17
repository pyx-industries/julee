"""Tests for Story domain model."""

import pytest
from pydantic import ValidationError

from julee.docs.sphinx_hcd.domain.models.story import Story


class TestStoryCreation:
    """Test Story model creation and validation."""

    def test_create_story_with_required_fields(self) -> None:
        """Test creating a story with minimum required fields."""
        story = Story(
            slug="submit-order",
            feature_title="Submit Order",
            persona="Customer",
            app_slug="checkout-app",
            file_path="tests/e2e/checkout-app/features/submit_order.feature",
        )

        assert story.slug == "submit-order"
        assert story.feature_title == "Submit Order"
        assert story.persona == "Customer"
        assert story.app_slug == "checkout-app"
        assert story.file_path == "tests/e2e/checkout-app/features/submit_order.feature"

    def test_create_story_with_all_fields(self) -> None:
        """Test creating a story with all fields."""
        story = Story(
            slug="submit-order",
            feature_title="Submit Order",
            persona="Customer",
            persona_normalized="customer",
            i_want="submit my order",
            so_that="I can purchase products",
            app_slug="checkout-app",
            app_normalized="checkout app",
            file_path="tests/e2e/checkout-app/features/submit.feature",
            abs_path="/abs/path/to/submit.feature",
            gherkin_snippet="Feature: Submit Order\n  As a Customer",
        )

        assert story.slug == "submit-order"
        assert story.persona_normalized == "customer"
        assert story.i_want == "submit my order"
        assert story.so_that == "I can purchase products"
        assert story.gherkin_snippet == "Feature: Submit Order\n  As a Customer"

    def test_normalized_fields_computed_automatically(self) -> None:
        """Test that normalized fields are computed from raw values."""
        story = Story(
            slug="test",
            feature_title="Test Feature",
            persona="Staff Member",
            app_slug="Staff-Portal",
            file_path="test.feature",
        )

        assert story.persona_normalized == "staff member"
        assert story.app_normalized == "staff portal"

    def test_empty_slug_raises_error(self) -> None:
        """Test that empty slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            Story(
                slug="",
                feature_title="Test",
                persona="User",
                app_slug="app",
                file_path="test.feature",
            )

    def test_empty_feature_title_raises_error(self) -> None:
        """Test that empty feature title raises validation error."""
        with pytest.raises(ValidationError, match="Feature title cannot be empty"):
            Story(
                slug="test",
                feature_title="",
                persona="User",
                app_slug="app",
                file_path="test.feature",
            )

    def test_empty_persona_defaults_to_unknown(self) -> None:
        """Test that empty persona defaults to 'unknown'."""
        story = Story(
            slug="test",
            feature_title="Test",
            persona="",
            app_slug="app",
            file_path="test.feature",
        )
        assert story.persona == "unknown"

    def test_empty_app_slug_defaults_to_unknown(self) -> None:
        """Test that empty app slug defaults to 'unknown'."""
        story = Story(
            slug="test",
            feature_title="Test",
            persona="User",
            app_slug="",
            file_path="test.feature",
        )
        assert story.app_slug == "unknown"

    def test_whitespace_only_slug_raises_error(self) -> None:
        """Test that whitespace-only slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            Story(
                slug="   ",
                feature_title="Test",
                persona="User",
                app_slug="app",
                file_path="test.feature",
            )


class TestStoryFromFeatureFile:
    """Test Story.from_feature_file factory method."""

    def test_from_feature_file_creates_story(self) -> None:
        """Test creating a story from feature file data."""
        story = Story.from_feature_file(
            feature_title="Upload Document",
            persona="Staff Member",
            i_want="upload a document",
            so_that="it can be analyzed",
            app_slug="staff-portal",
            file_path="tests/e2e/staff-portal/features/upload.feature",
            abs_path="/home/project/tests/e2e/staff-portal/features/upload.feature",
            gherkin_snippet="Feature: Upload Document",
        )

        assert story.slug == "upload-document"  # Auto-slugified
        assert story.feature_title == "Upload Document"
        assert story.persona == "Staff Member"
        assert story.persona_normalized == "staff member"
        assert story.i_want == "upload a document"
        assert story.so_that == "it can be analyzed"
        assert story.app_slug == "staff-portal"


class TestStoryMatching:
    """Test Story matching methods."""

    @pytest.fixture
    def sample_story(self) -> Story:
        """Create a sample story for testing."""
        return Story(
            slug="test-story",
            feature_title="Test Story",
            persona="Staff Member",
            app_slug="staff-portal",
            file_path="test.feature",
        )

    def test_matches_persona_exact(self, sample_story: Story) -> None:
        """Test persona matching with exact name."""
        assert sample_story.matches_persona("Staff Member") is True

    def test_matches_persona_case_insensitive(self, sample_story: Story) -> None:
        """Test persona matching is case-insensitive."""
        assert sample_story.matches_persona("staff member") is True
        assert sample_story.matches_persona("STAFF MEMBER") is True

    def test_matches_persona_no_match(self, sample_story: Story) -> None:
        """Test persona matching returns False for non-match."""
        assert sample_story.matches_persona("Customer") is False

    def test_matches_app_exact(self, sample_story: Story) -> None:
        """Test app matching with exact name."""
        assert sample_story.matches_app("staff-portal") is True

    def test_matches_app_with_different_separators(self, sample_story: Story) -> None:
        """Test app matching handles different separators."""
        assert sample_story.matches_app("staff portal") is True
        assert sample_story.matches_app("Staff Portal") is True

    def test_matches_app_no_match(self, sample_story: Story) -> None:
        """Test app matching returns False for non-match."""
        assert sample_story.matches_app("checkout-app") is False


class TestStorySerialization:
    """Test Story serialization."""

    def test_story_to_dict(self) -> None:
        """Test story can be serialized to dict."""
        story = Story(
            slug="test",
            feature_title="Test",
            persona="User",
            app_slug="app",
            file_path="test.feature",
        )

        data = story.model_dump()
        assert data["slug"] == "test"
        assert data["feature_title"] == "Test"
        assert data["persona"] == "User"

    def test_story_to_json(self) -> None:
        """Test story can be serialized to JSON."""
        story = Story(
            slug="test",
            feature_title="Test",
            persona="User",
            app_slug="app",
            file_path="test.feature",
        )

        json_str = story.model_dump_json()
        assert '"slug":"test"' in json_str
