"""Tests for Journey domain model."""

import pytest
from pydantic import ValidationError

from julee.hcd.entities.journey import (
    Journey,
    JourneyStep,
    StepType,
)


class TestStepType:
    """Test StepType enum."""

    def test_step_type_values(self) -> None:
        """Test StepType enum values."""
        assert StepType.STORY.value == "story"
        assert StepType.EPIC.value == "epic"
        assert StepType.PHASE.value == "phase"

    def test_from_string_valid(self) -> None:
        """Test from_string with valid values."""
        assert StepType.from_string("story") == StepType.STORY
        assert StepType.from_string("epic") == StepType.EPIC
        assert StepType.from_string("phase") == StepType.PHASE

    def test_from_string_case_insensitive(self) -> None:
        """Test from_string is case-insensitive."""
        assert StepType.from_string("STORY") == StepType.STORY
        assert StepType.from_string("Epic") == StepType.EPIC

    def test_from_string_invalid(self) -> None:
        """Test from_string raises for invalid values."""
        with pytest.raises(ValueError, match="Invalid step type"):
            StepType.from_string("invalid")


class TestJourneyStep:
    """Test JourneyStep model."""

    def test_create_story_step(self) -> None:
        """Test creating a story step."""
        step = JourneyStep(step_type=StepType.STORY, ref="Upload Document")
        assert step.step_type == StepType.STORY
        assert step.ref == "Upload Document"
        assert step.is_story is True
        assert step.is_epic is False
        assert step.is_phase is False

    def test_create_epic_step(self) -> None:
        """Test creating an epic step."""
        step = JourneyStep(step_type=StepType.EPIC, ref="vocabulary-management")
        assert step.step_type == StepType.EPIC
        assert step.ref == "vocabulary-management"
        assert step.is_epic is True

    def test_create_phase_step(self) -> None:
        """Test creating a phase step with description."""
        step = JourneyStep(
            step_type=StepType.PHASE,
            ref="Upload Sources",
            description="Add reference materials to the knowledge base.",
        )
        assert step.step_type == StepType.PHASE
        assert step.ref == "Upload Sources"
        assert step.description == "Add reference materials to the knowledge base."
        assert step.is_phase is True

    def test_empty_ref_raises_error(self) -> None:
        """Test that empty ref raises validation error."""
        with pytest.raises(ValidationError, match="ref cannot be empty"):
            JourneyStep(step_type=StepType.STORY, ref="")

    def test_story_factory(self) -> None:
        """Test story factory method."""
        step = JourneyStep.story("Upload Document")
        assert step.step_type == StepType.STORY
        assert step.ref == "Upload Document"

    def test_epic_factory(self) -> None:
        """Test epic factory method."""
        step = JourneyStep.epic("vocabulary-management")
        assert step.step_type == StepType.EPIC
        assert step.ref == "vocabulary-management"

    def test_phase_factory(self) -> None:
        """Test phase factory method."""
        step = JourneyStep.phase("Upload Sources", "Add materials.")
        assert step.step_type == StepType.PHASE
        assert step.ref == "Upload Sources"
        assert step.description == "Add materials."

    def test_phase_factory_without_description(self) -> None:
        """Test phase factory without description."""
        step = JourneyStep.phase("Upload Sources")
        assert step.description == ""


class TestJourneyCreation:
    """Test Journey model creation and validation."""

    def test_create_journey_minimal(self) -> None:
        """Test creating a journey with minimum fields."""
        journey = Journey(slug="build-vocabulary")
        assert journey.slug == "build-vocabulary"
        assert journey.persona == ""
        assert journey.steps == []
        assert journey.depends_on == []

    def test_create_journey_complete(self) -> None:
        """Test creating a journey with all fields."""
        steps = [
            JourneyStep.story("Upload Document"),
            JourneyStep.epic("vocabulary-management"),
        ]
        journey = Journey(
            slug="build-vocabulary",
            persona="Knowledge Curator",
            intent="Ensure consistent terminology across programs",
            outcome="Semantic interoperability enabling compliance mapping",
            goal="Create a Sustainable Vocabulary Catalog",
            depends_on=["operate-pipelines", "setup-system"],
            steps=steps,
            preconditions=["Source materials available", "SME accessible"],
            postconditions=["SVC published and versioned"],
            docname="journeys/build-vocabulary",
        )

        assert journey.slug == "build-vocabulary"
        assert journey.persona == "Knowledge Curator"
        assert journey.persona_normalized == "knowledge curator"
        assert journey.intent == "Ensure consistent terminology across programs"
        assert len(journey.steps) == 2
        assert len(journey.depends_on) == 2
        assert journey.docname == "journeys/build-vocabulary"

    def test_persona_normalized_computed(self) -> None:
        """Test that persona_normalized is computed."""
        journey = Journey(slug="test", persona="Knowledge Curator")
        assert journey.persona_normalized == "knowledge curator"

    def test_empty_slug_raises_error(self) -> None:
        """Test that empty slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            Journey(slug="")


class TestJourneyMatching:
    """Test Journey matching methods."""

    @pytest.fixture
    def sample_journey(self) -> Journey:
        """Create a sample journey for testing."""
        return Journey(
            slug="build-vocabulary",
            persona="Knowledge Curator",
            depends_on=["operate-pipelines", "setup-system"],
            steps=[
                JourneyStep.story("Upload Document"),
                JourneyStep.epic("vocabulary-management"),
                JourneyStep.story("Review Vocabulary"),
            ],
        )

    def test_matches_persona_exact(self, sample_journey: Journey) -> None:
        """Test persona matching with exact name."""
        assert sample_journey.matches_persona("Knowledge Curator") is True

    def test_matches_persona_case_insensitive(self, sample_journey: Journey) -> None:
        """Test persona matching is case-insensitive."""
        assert sample_journey.matches_persona("knowledge curator") is True
        assert sample_journey.matches_persona("KNOWLEDGE CURATOR") is True

    def test_matches_persona_no_match(self, sample_journey: Journey) -> None:
        """Test persona matching returns False for non-match."""
        assert sample_journey.matches_persona("Analyst") is False

    def test_has_dependency(self, sample_journey: Journey) -> None:
        """Test dependency checking."""
        assert sample_journey.has_dependency("operate-pipelines") is True
        assert sample_journey.has_dependency("setup-system") is True
        assert sample_journey.has_dependency("unknown") is False

    def test_get_story_refs(self, sample_journey: Journey) -> None:
        """Test getting story references."""
        refs = sample_journey.get_story_refs()
        assert refs == ["Upload Document", "Review Vocabulary"]

    def test_get_epic_refs(self, sample_journey: Journey) -> None:
        """Test getting epic references."""
        refs = sample_journey.get_epic_refs()
        assert refs == ["vocabulary-management"]


class TestJourneySteps:
    """Test Journey step operations."""

    def test_add_step(self) -> None:
        """Test adding a step."""
        journey = Journey(slug="test")
        assert journey.step_count == 0

        journey.add_step(JourneyStep.story("Test Story"))
        assert journey.step_count == 1
        assert journey.has_steps is True

    def test_has_steps_empty(self) -> None:
        """Test has_steps with empty journey."""
        journey = Journey(slug="test")
        assert journey.has_steps is False


class TestJourneyProperties:
    """Test Journey properties."""

    def test_display_title(self) -> None:
        """Test display_title property."""
        journey = Journey(slug="build-vocabulary")
        assert journey.display_title == "Build Vocabulary"

    def test_display_title_multiple_words(self) -> None:
        """Test display_title with multiple hyphens."""
        journey = Journey(slug="operate-data-pipelines")
        assert journey.display_title == "Operate Data Pipelines"


class TestJourneySerialization:
    """Test Journey serialization."""

    def test_journey_to_dict(self) -> None:
        """Test journey can be serialized to dict."""
        journey = Journey(
            slug="test",
            persona="User",
            steps=[JourneyStep.story("Test Story")],
        )

        data = journey.model_dump()
        assert data["slug"] == "test"
        assert data["persona"] == "User"
        assert len(data["steps"]) == 1
        assert data["steps"][0]["step_type"] == StepType.STORY

    def test_journey_to_json(self) -> None:
        """Test journey can be serialized to JSON."""
        journey = Journey(slug="test", persona="User")
        json_str = journey.model_dump_json()
        assert '"slug":"test"' in json_str
