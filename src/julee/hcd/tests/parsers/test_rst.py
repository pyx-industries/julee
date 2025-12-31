"""Tests for RST directive parsers."""

from pathlib import Path

from julee.supply_chain.entities.accelerator import (
    Accelerator,
    IntegrationReference,
)
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.journey import Journey, JourneyStep, StepType
from julee.hcd.parsers.rst import (
    parse_accelerator_content,
    parse_accelerator_file,
    parse_epic_content,
    parse_epic_file,
    parse_journey_content,
    parse_journey_file,
    scan_accelerator_directory,
    scan_epic_directory,
    scan_journey_directory,
)
from julee.hcd.serializers.rst import (
    serialize_accelerator,
    serialize_epic,
    serialize_journey,
)

# =============================================================================
# Epic Parser Tests
# =============================================================================


class TestParseEpicContent:
    """Test parse_epic_content function."""

    def test_parse_simple_epic(self) -> None:
        """Test parsing a simple epic directive."""
        content = """.. define-epic:: user-onboarding

   This epic covers the user onboarding flow.

.. epic-story:: create-account
.. epic-story:: verify-email
"""
        result = parse_epic_content(content)

        assert result is not None
        assert result.slug == "user-onboarding"
        assert "user onboarding flow" in result.description
        assert result.story_refs == ["create-account", "verify-email"]

    def test_parse_epic_no_stories(self) -> None:
        """Test parsing epic with no story references."""
        content = """.. define-epic:: empty-epic

   An epic without any stories.
"""
        result = parse_epic_content(content)

        assert result is not None
        assert result.slug == "empty-epic"
        assert "without any stories" in result.description
        assert result.story_refs == []

    def test_parse_epic_multiline_description(self) -> None:
        """Test parsing epic with multi-line description."""
        content = """.. define-epic:: complex-epic

   This is the first line.
   This is the second line.

   This is after a blank line.

.. epic-story:: feature-one
"""
        result = parse_epic_content(content)

        assert result is not None
        assert "first line" in result.description
        assert "second line" in result.description
        assert "after a blank line" in result.description

    def test_parse_epic_no_directive(self) -> None:
        """Test parsing content without epic directive returns None."""
        content = """This is just regular RST content.

Nothing to see here.
"""
        result = parse_epic_content(content)
        assert result is None

    def test_parse_epic_with_extra_whitespace(self) -> None:
        """Test parsing handles extra whitespace in slug."""
        content = """.. define-epic::   trimmed-slug

   Description here.
"""
        result = parse_epic_content(content)

        assert result is not None
        assert result.slug == "trimmed-slug"


class TestParseEpicFile:
    """Test parse_epic_file function."""

    def test_parse_valid_file(self, tmp_path: Path) -> None:
        """Test parsing a valid RST file."""
        epic_file = tmp_path / "test-epic.rst"
        epic_file.write_text(
            """.. define-epic:: test-epic

   Test description.

.. epic-story:: story-one
"""
        )
        result = parse_epic_file(epic_file)

        assert result is not None
        assert isinstance(result, Epic)
        assert result.slug == "test-epic"
        assert result.story_refs == ["story-one"]

    def test_parse_nonexistent_file(self, tmp_path: Path) -> None:
        """Test parsing nonexistent file returns None."""
        result = parse_epic_file(tmp_path / "nonexistent.rst")
        assert result is None

    def test_parse_file_no_directive(self, tmp_path: Path) -> None:
        """Test parsing file without directive returns None."""
        rst_file = tmp_path / "no-directive.rst"
        rst_file.write_text("Just regular RST.\n")

        result = parse_epic_file(rst_file)
        assert result is None


class TestScanEpicDirectory:
    """Test scan_epic_directory function."""

    def test_scan_finds_all_epics(self, tmp_path: Path) -> None:
        """Test scanning finds all epic files."""
        (tmp_path / "epic1.rst").write_text(
            ".. define-epic:: epic-one\n\n   First epic.\n"
        )
        (tmp_path / "epic2.rst").write_text(
            ".. define-epic:: epic-two\n\n   Second epic.\n"
        )

        epics = scan_epic_directory(tmp_path)

        assert len(epics) == 2
        slugs = {e.slug for e in epics}
        assert slugs == {"epic-one", "epic-two"}

    def test_scan_skips_invalid_files(self, tmp_path: Path) -> None:
        """Test scanning skips files without epic directive."""
        (tmp_path / "valid.rst").write_text(".. define-epic:: valid\n\n   Valid.\n")
        (tmp_path / "invalid.rst").write_text("No directive here.\n")

        epics = scan_epic_directory(tmp_path)

        assert len(epics) == 1
        assert epics[0].slug == "valid"

    def test_scan_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test scanning nonexistent directory returns empty list."""
        epics = scan_epic_directory(tmp_path / "nonexistent")
        assert epics == []


class TestEpicRoundTrip:
    """Test serialize -> parse round-trip for epics."""

    def test_round_trip_simple(self, tmp_path: Path) -> None:
        """Test simple epic round-trip."""
        original = Epic(
            slug="round-trip-epic",
            description="Test round-trip serialization.",
            story_refs=["story-a", "story-b"],
        )

        # Serialize and write
        content = serialize_epic(original)
        file_path = tmp_path / "round-trip.rst"
        file_path.write_text(content)

        # Parse back
        parsed = parse_epic_file(file_path)

        assert parsed is not None
        assert parsed.slug == original.slug
        assert parsed.description == original.description
        assert parsed.story_refs == original.story_refs


# =============================================================================
# Journey Parser Tests
# =============================================================================


class TestParseJourneyContent:
    """Test parse_journey_content function."""

    def test_parse_simple_journey(self) -> None:
        """Test parsing a simple journey directive."""
        content = """.. define-journey:: new-user-signup
   :persona: New User
   :intent: Create an account
   :outcome: Successfully registered

   Complete the signup process to access the application.

.. step-phase:: Registration
.. step-story:: create-account
.. step-story:: verify-email
"""
        result = parse_journey_content(content)

        assert result is not None
        assert result.slug == "new-user-signup"
        assert result.persona == "New User"
        assert result.intent == "Create an account"
        assert result.outcome == "Successfully registered"
        assert "signup process" in result.goal
        assert len(result.steps) == 3

    def test_parse_journey_with_depends_on(self) -> None:
        """Test parsing journey with dependencies."""
        content = """.. define-journey:: advanced-setup
   :persona: Power User
   :depends-on: basic-setup, initial-config
   :preconditions: Account verified
                   Email confirmed
   :postconditions: Ready to use advanced features

   Configure advanced options.
"""
        result = parse_journey_content(content)

        assert result is not None
        assert result.depends_on == ["basic-setup", "initial-config"]
        assert "Account verified" in result.preconditions
        assert "Email confirmed" in result.preconditions
        assert "Ready to use advanced features" in result.postconditions

    def test_parse_journey_steps(self) -> None:
        """Test parsing journey step types."""
        content = """.. define-journey:: mixed-steps
   :persona: User

   Journey with mixed step types.

.. step-phase:: Phase One
   Description of phase one.

.. step-story:: do-something
.. step-epic:: complete-epic
"""
        result = parse_journey_content(content)

        assert result is not None
        assert len(result.steps) == 3

        # Check step types
        assert result.steps[0].step_type == StepType.PHASE
        assert result.steps[0].ref == "Phase One"
        assert "Description of phase one" in result.steps[0].description

        assert result.steps[1].step_type == StepType.STORY
        assert result.steps[1].ref == "do-something"

        assert result.steps[2].step_type == StepType.EPIC
        assert result.steps[2].ref == "complete-epic"

    def test_parse_journey_no_directive(self) -> None:
        """Test parsing content without journey directive."""
        content = "Regular RST content."
        result = parse_journey_content(content)
        assert result is None


class TestParseJourneyFile:
    """Test parse_journey_file function."""

    def test_parse_valid_file(self, tmp_path: Path) -> None:
        """Test parsing a valid journey RST file."""
        journey_file = tmp_path / "test-journey.rst"
        journey_file.write_text(
            """.. define-journey:: test-journey
   :persona: Tester
   :intent: Test parsing

   Goal description.

.. step-story:: test-step
"""
        )
        result = parse_journey_file(journey_file)

        assert result is not None
        assert isinstance(result, Journey)
        assert result.slug == "test-journey"
        assert result.persona == "Tester"

    def test_parse_nonexistent_file(self, tmp_path: Path) -> None:
        """Test parsing nonexistent file returns None."""
        result = parse_journey_file(tmp_path / "nonexistent.rst")
        assert result is None


class TestScanJourneyDirectory:
    """Test scan_journey_directory function."""

    def test_scan_finds_all_journeys(self, tmp_path: Path) -> None:
        """Test scanning finds all journey files."""
        (tmp_path / "journey1.rst").write_text(
            ".. define-journey:: journey-one\n   :persona: User\n\n   First.\n"
        )
        (tmp_path / "journey2.rst").write_text(
            ".. define-journey:: journey-two\n   :persona: Admin\n\n   Second.\n"
        )

        journeys = scan_journey_directory(tmp_path)

        assert len(journeys) == 2
        slugs = {j.slug for j in journeys}
        assert slugs == {"journey-one", "journey-two"}

    def test_scan_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test scanning nonexistent directory returns empty list."""
        journeys = scan_journey_directory(tmp_path / "nonexistent")
        assert journeys == []


class TestJourneyRoundTrip:
    """Test serialize -> parse round-trip for journeys."""

    def test_round_trip_simple(self, tmp_path: Path) -> None:
        """Test simple journey round-trip."""
        original = Journey(
            slug="round-trip-journey",
            persona="Round Trip User",
            intent="Test serialization",
            outcome="Verified correctness",
            goal="Ensure round-trip works.",
            steps=[
                JourneyStep(step_type=StepType.STORY, ref="test-story"),
            ],
        )

        # Serialize and write
        content = serialize_journey(original)
        file_path = tmp_path / "round-trip.rst"
        file_path.write_text(content)

        # Parse back
        parsed = parse_journey_file(file_path)

        assert parsed is not None
        assert parsed.slug == original.slug
        assert parsed.persona == original.persona
        assert parsed.intent == original.intent
        assert parsed.outcome == original.outcome
        assert len(parsed.steps) == 1


# =============================================================================
# Accelerator Parser Tests
# =============================================================================


class TestParseAcceleratorContent:
    """Test parse_accelerator_content function."""

    def test_parse_simple_accelerator(self) -> None:
        """Test parsing a simple accelerator directive."""
        content = """.. define-accelerator:: api-gateway
   :status: Active
   :milestone: v1.0
   :acceptance: All tests pass

   Provide unified API access.
"""
        result = parse_accelerator_content(content)

        assert result is not None
        assert result.slug == "api-gateway"
        assert result.status == "Active"
        assert result.milestone == "v1.0"
        assert result.acceptance == "All tests pass"
        assert "unified API" in result.objective

    def test_parse_accelerator_with_integrations(self) -> None:
        """Test parsing accelerator with integration references."""
        content = """.. define-accelerator:: data-processor
   :sources-from: raw-data-source, external-feed
   :publishes-to: processed-data, analytics-sink
   :depends-on: auth-service
   :feeds-into: reporting-service

   Process data from multiple sources.
"""
        result = parse_accelerator_content(content)

        assert result is not None
        assert result.sources_from == ["raw-data-source", "external-feed"]
        assert result.publishes_to == ["processed-data", "analytics-sink"]
        assert result.depends_on == ["auth-service"]
        assert result.feeds_into == ["reporting-service"]

    def test_parse_accelerator_no_directive(self) -> None:
        """Test parsing content without accelerator directive."""
        content = "No accelerator here."
        result = parse_accelerator_content(content)
        assert result is None


class TestParseAcceleratorFile:
    """Test parse_accelerator_file function."""

    def test_parse_valid_file(self, tmp_path: Path) -> None:
        """Test parsing a valid accelerator RST file."""
        accel_file = tmp_path / "test-accel.rst"
        accel_file.write_text(
            """.. define-accelerator:: test-accel
   :status: Draft

   Test accelerator.
"""
        )
        result = parse_accelerator_file(accel_file)

        assert result is not None
        assert isinstance(result, Accelerator)
        assert result.slug == "test-accel"
        assert result.status == "Draft"

    def test_parse_nonexistent_file(self, tmp_path: Path) -> None:
        """Test parsing nonexistent file returns None."""
        result = parse_accelerator_file(tmp_path / "nonexistent.rst")
        assert result is None


class TestScanAcceleratorDirectory:
    """Test scan_accelerator_directory function."""

    def test_scan_finds_all_accelerators(self, tmp_path: Path) -> None:
        """Test scanning finds all accelerator files."""
        (tmp_path / "accel1.rst").write_text(
            ".. define-accelerator:: accel-one\n   :status: Active\n\n   First.\n"
        )
        (tmp_path / "accel2.rst").write_text(
            ".. define-accelerator:: accel-two\n   :status: Draft\n\n   Second.\n"
        )

        accels = scan_accelerator_directory(tmp_path)

        assert len(accels) == 2
        slugs = {a.slug for a in accels}
        assert slugs == {"accel-one", "accel-two"}

    def test_scan_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test scanning nonexistent directory returns empty list."""
        accels = scan_accelerator_directory(tmp_path / "nonexistent")
        assert accels == []


class TestAcceleratorRoundTrip:
    """Test serialize -> parse round-trip for accelerators."""

    def test_round_trip_simple(self, tmp_path: Path) -> None:
        """Test simple accelerator round-trip."""
        original = Accelerator(
            slug="round-trip-accel",
            status="Active",
            milestone="v2.0",
            acceptance="Verified",
            objective="Test round-trip.",
            sources_from=[IntegrationReference(slug="source-int")],
            publishes_to=[IntegrationReference(slug="target-int")],
            depends_on=["dep-accel"],
            feeds_into=["consumer-accel"],
        )

        # Serialize and write
        content = serialize_accelerator(original)
        file_path = tmp_path / "round-trip.rst"
        file_path.write_text(content)

        # Parse back
        parsed = parse_accelerator_file(file_path)

        assert parsed is not None
        assert parsed.slug == original.slug
        assert parsed.status == original.status
        assert parsed.objective == original.objective
        assert len(parsed.sources_from) == 1
        assert parsed.sources_from[0].slug == "source-int"
