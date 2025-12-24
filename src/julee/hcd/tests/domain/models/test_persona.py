"""Tests for Persona domain model."""

import pytest
from pydantic import ValidationError

from julee.hcd.domain.models.persona import Persona


class TestPersonaCreation:
    """Test Persona model creation and validation."""

    def test_create_persona_minimal(self) -> None:
        """Test creating a persona with minimum fields."""
        persona = Persona(name="Knowledge Curator")
        assert persona.name == "Knowledge Curator"
        assert persona.app_slugs == []
        assert persona.epic_slugs == []

    def test_create_persona_complete(self) -> None:
        """Test creating a persona with all fields."""
        persona = Persona(
            name="Knowledge Curator",
            app_slugs=["vocabulary-tool", "admin-portal"],
            epic_slugs=["vocabulary-management", "credential-creation"],
        )

        assert persona.name == "Knowledge Curator"
        assert len(persona.app_slugs) == 2
        assert len(persona.epic_slugs) == 2

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError, match="name cannot be empty"):
            Persona(name="")

    def test_whitespace_name_raises_error(self) -> None:
        """Test that whitespace-only name raises validation error."""
        with pytest.raises(ValidationError, match="name cannot be empty"):
            Persona(name="   ")

    def test_name_stripped(self) -> None:
        """Test that name is stripped of whitespace."""
        persona = Persona(name="  Knowledge Curator  ")
        assert persona.name == "Knowledge Curator"


class TestPersonaProperties:
    """Test Persona properties."""

    @pytest.fixture
    def sample_persona(self) -> Persona:
        """Create a sample persona for testing."""
        return Persona(
            name="Knowledge Curator",
            app_slugs=["vocabulary-tool", "admin-portal"],
            epic_slugs=["vocabulary-management", "credential-creation"],
        )

    def test_normalized_name(self, sample_persona: Persona) -> None:
        """Test normalized_name computed field."""
        assert sample_persona.normalized_name == "knowledge curator"

    def test_display_name(self, sample_persona: Persona) -> None:
        """Test display_name property."""
        assert sample_persona.display_name == "Knowledge Curator"

    def test_app_count(self, sample_persona: Persona) -> None:
        """Test app_count property."""
        assert sample_persona.app_count == 2

    def test_epic_count(self, sample_persona: Persona) -> None:
        """Test epic_count property."""
        assert sample_persona.epic_count == 2

    def test_has_apps_true(self, sample_persona: Persona) -> None:
        """Test has_apps property when true."""
        assert sample_persona.has_apps is True

    def test_has_apps_false(self) -> None:
        """Test has_apps property when false."""
        persona = Persona(name="Test")
        assert persona.has_apps is False

    def test_has_epics_true(self, sample_persona: Persona) -> None:
        """Test has_epics property when true."""
        assert sample_persona.has_epics is True

    def test_has_epics_false(self) -> None:
        """Test has_epics property when false."""
        persona = Persona(name="Test")
        assert persona.has_epics is False


class TestPersonaMethods:
    """Test Persona methods."""

    @pytest.fixture
    def sample_persona(self) -> Persona:
        """Create a sample persona for testing."""
        return Persona(
            name="Knowledge Curator",
            app_slugs=["vocabulary-tool", "admin-portal"],
            epic_slugs=["vocabulary-management"],
        )

    def test_uses_app_true(self, sample_persona: Persona) -> None:
        """Test uses_app returns True for used app."""
        assert sample_persona.uses_app("vocabulary-tool") is True
        assert sample_persona.uses_app("admin-portal") is True

    def test_uses_app_false(self, sample_persona: Persona) -> None:
        """Test uses_app returns False for unused app."""
        assert sample_persona.uses_app("unknown-app") is False

    def test_participates_in_epic_true(self, sample_persona: Persona) -> None:
        """Test participates_in_epic returns True."""
        assert sample_persona.participates_in_epic("vocabulary-management") is True

    def test_participates_in_epic_false(self, sample_persona: Persona) -> None:
        """Test participates_in_epic returns False."""
        assert sample_persona.participates_in_epic("unknown-epic") is False

    def test_add_app_new(self) -> None:
        """Test adding a new app."""
        persona = Persona(name="Test")
        persona.add_app("new-app")
        assert "new-app" in persona.app_slugs
        assert persona.app_count == 1

    def test_add_app_duplicate(self, sample_persona: Persona) -> None:
        """Test adding a duplicate app is ignored."""
        initial_count = sample_persona.app_count
        sample_persona.add_app("vocabulary-tool")
        assert sample_persona.app_count == initial_count

    def test_add_epic_new(self) -> None:
        """Test adding a new epic."""
        persona = Persona(name="Test")
        persona.add_epic("new-epic")
        assert "new-epic" in persona.epic_slugs
        assert persona.epic_count == 1

    def test_add_epic_duplicate(self, sample_persona: Persona) -> None:
        """Test adding a duplicate epic is ignored."""
        initial_count = sample_persona.epic_count
        sample_persona.add_epic("vocabulary-management")
        assert sample_persona.epic_count == initial_count


class TestPersonaSerialization:
    """Test Persona serialization."""

    def test_persona_to_dict(self) -> None:
        """Test persona can be serialized to dict."""
        persona = Persona(
            name="Test Persona",
            app_slugs=["app-1"],
            epic_slugs=["epic-1"],
        )

        data = persona.model_dump()
        assert data["name"] == "Test Persona"
        assert data["app_slugs"] == ["app-1"]
        assert data["epic_slugs"] == ["epic-1"]
        assert data["normalized_name"] == "test persona"

    def test_persona_to_json(self) -> None:
        """Test persona can be serialized to JSON."""
        persona = Persona(name="Test Persona")
        json_str = persona.model_dump_json()
        assert '"name":"Test Persona"' in json_str
        assert '"normalized_name":"test persona"' in json_str
