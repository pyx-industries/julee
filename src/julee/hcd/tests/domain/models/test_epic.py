"""Tests for Epic domain model."""

import pytest
from pydantic import ValidationError

from julee.hcd.entities.epic import Epic


class TestEpicCreation:
    """Test Epic model creation and validation."""

    def test_create_epic_minimal(self) -> None:
        """Test creating an epic with minimum fields."""
        epic = Epic(slug="vocabulary-management")
        assert epic.slug == "vocabulary-management"
        assert epic.description == ""
        assert epic.story_refs == []
        assert epic.docname == ""

    def test_create_epic_complete(self) -> None:
        """Test creating an epic with all fields."""
        epic = Epic(
            slug="vocabulary-management",
            description="Manage terminology and vocabulary catalogs",
            story_refs=["Upload Document", "Review Vocabulary", "Publish Catalog"],
            docname="epics/vocabulary-management",
        )

        assert epic.slug == "vocabulary-management"
        assert epic.description == "Manage terminology and vocabulary catalogs"
        assert len(epic.story_refs) == 3
        assert epic.docname == "epics/vocabulary-management"

    def test_empty_slug_raises_error(self) -> None:
        """Test that empty slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            Epic(slug="")

    def test_whitespace_slug_raises_error(self) -> None:
        """Test that whitespace-only slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            Epic(slug="   ")

    def test_slug_stripped(self) -> None:
        """Test that slug is stripped of whitespace."""
        epic = Epic(slug="  vocabulary-management  ")
        assert epic.slug == "vocabulary-management"


class TestEpicStoryOperations:
    """Test Epic story reference operations."""

    @pytest.fixture
    def sample_epic(self) -> Epic:
        """Create a sample epic for testing."""
        return Epic(
            slug="vocabulary-management",
            description="Manage terminology",
            story_refs=["Upload Document", "Review Vocabulary"],
            docname="epics/vocabulary-management",
        )

    def test_add_story(self) -> None:
        """Test adding a story to an epic."""
        epic = Epic(slug="test-epic")
        assert epic.story_count == 0

        epic.add_story("New Story")
        assert epic.story_count == 1
        assert "New Story" in epic.story_refs

    def test_has_story_exact_match(self, sample_epic: Epic) -> None:
        """Test has_story with exact match."""
        assert sample_epic.has_story("Upload Document") is True
        assert sample_epic.has_story("Review Vocabulary") is True

    def test_has_story_case_insensitive(self, sample_epic: Epic) -> None:
        """Test has_story is case-insensitive."""
        assert sample_epic.has_story("upload document") is True
        assert sample_epic.has_story("UPLOAD DOCUMENT") is True
        assert sample_epic.has_story("Upload document") is True

    def test_has_story_no_match(self, sample_epic: Epic) -> None:
        """Test has_story returns False for non-match."""
        assert sample_epic.has_story("Unknown Story") is False

    def test_get_story_refs_normalized(self, sample_epic: Epic) -> None:
        """Test getting normalized story references."""
        normalized = sample_epic.get_story_refs_normalized()
        assert normalized == ["upload document", "review vocabulary"]


class TestEpicProperties:
    """Test Epic properties."""

    def test_display_title(self) -> None:
        """Test display_title property."""
        epic = Epic(slug="vocabulary-management")
        assert epic.display_title == "Vocabulary Management"

    def test_display_title_multiple_words(self) -> None:
        """Test display_title with multiple hyphens."""
        epic = Epic(slug="credential-creation-workflow")
        assert epic.display_title == "Credential Creation Workflow"

    def test_story_count_empty(self) -> None:
        """Test story_count with no stories."""
        epic = Epic(slug="test")
        assert epic.story_count == 0

    def test_story_count_with_stories(self) -> None:
        """Test story_count with stories."""
        epic = Epic(slug="test", story_refs=["Story 1", "Story 2", "Story 3"])
        assert epic.story_count == 3

    def test_has_stories_empty(self) -> None:
        """Test has_stories with no stories."""
        epic = Epic(slug="test")
        assert epic.has_stories is False

    def test_has_stories_with_stories(self) -> None:
        """Test has_stories with stories."""
        epic = Epic(slug="test", story_refs=["Story 1"])
        assert epic.has_stories is True


class TestEpicSerialization:
    """Test Epic serialization."""

    def test_epic_to_dict(self) -> None:
        """Test epic can be serialized to dict."""
        epic = Epic(
            slug="test",
            description="Test description",
            story_refs=["Story 1"],
            docname="test/doc",
        )

        data = epic.model_dump()
        assert data["slug"] == "test"
        assert data["description"] == "Test description"
        assert data["story_refs"] == ["Story 1"]
        assert data["docname"] == "test/doc"

    def test_epic_to_json(self) -> None:
        """Test epic can be serialized to JSON."""
        epic = Epic(slug="test", description="Test")
        json_str = epic.model_dump_json()
        assert '"slug":"test"' in json_str
        assert '"description":"Test"' in json_str

    def test_epic_from_dict(self) -> None:
        """Test epic can be deserialized from dict."""
        data = {
            "slug": "test",
            "description": "Test description",
            "story_refs": ["Story 1", "Story 2"],
            "docname": "test/doc",
        }
        epic = Epic.model_validate(data)
        assert epic.slug == "test"
        assert epic.description == "Test description"
        assert len(epic.story_refs) == 2
