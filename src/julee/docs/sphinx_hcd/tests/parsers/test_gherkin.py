"""Tests for Gherkin feature file parser."""

import tempfile
from pathlib import Path

import pytest

from julee.docs.sphinx_hcd.parsers.gherkin import (
    ParsedFeature,
    parse_feature_content,
    parse_feature_file,
    scan_feature_directory,
)


class TestParseFeatureContent:
    """Test parse_feature_content function."""

    def test_parse_complete_feature(self) -> None:
        """Test parsing a complete feature file."""
        content = """Feature: Submit Order

  As a Customer
  I want to submit my order
  So that I can purchase products

  Scenario: Successful submission
    Given I have items in my cart
    When I submit my order
    Then the order is confirmed
"""
        result = parse_feature_content(content)

        assert result.feature_title == "Submit Order"
        assert result.persona == "Customer"
        assert result.i_want == "submit my order"
        assert result.so_that == "I can purchase products"
        assert "Feature: Submit Order" in result.gherkin_snippet
        assert "As a Customer" in result.gherkin_snippet
        # Scenario should not be in snippet
        assert "Scenario" not in result.gherkin_snippet

    def test_parse_feature_with_as_an(self) -> None:
        """Test parsing 'As an' variant."""
        content = """Feature: Admin Dashboard

  As an Administrator
  I want to view the dashboard
  So that I can monitor the system
"""
        result = parse_feature_content(content)
        assert result.persona == "Administrator"

    def test_parse_feature_missing_persona(self) -> None:
        """Test parsing feature without persona defaults to 'unknown'."""
        content = """Feature: Some Feature

  I want to do something
  So that I achieve a goal
"""
        result = parse_feature_content(content)
        assert result.persona == "unknown"

    def test_parse_feature_missing_i_want(self) -> None:
        """Test parsing feature without I want defaults."""
        content = """Feature: Some Feature

  As a User
  So that I achieve a goal
"""
        result = parse_feature_content(content)
        assert result.i_want == "do something"

    def test_parse_feature_missing_so_that(self) -> None:
        """Test parsing feature without So that defaults."""
        content = """Feature: Some Feature

  As a User
  I want to do something
"""
        result = parse_feature_content(content)
        assert result.so_that == "achieve a goal"

    def test_parse_feature_missing_title(self) -> None:
        """Test parsing content without Feature line."""
        content = """
  As a User
  I want to do something
"""
        result = parse_feature_content(content)
        assert result.feature_title == "Unknown"

    def test_snippet_stops_at_background(self) -> None:
        """Test that snippet extraction stops at Background."""
        content = """Feature: Test

  As a User
  I want to test

  Background:
    Given some setup
"""
        result = parse_feature_content(content)
        assert "Background" not in result.gherkin_snippet

    def test_snippet_stops_at_tags(self) -> None:
        """Test that snippet extraction stops at tags."""
        content = """Feature: Test

  As a User
  I want to test

  @slow @integration
  Scenario: Tagged scenario
"""
        result = parse_feature_content(content)
        assert "@slow" not in result.gherkin_snippet

    def test_parse_indented_content(self) -> None:
        """Test parsing with various indentation."""
        content = """Feature: Upload Document

    As a Staff Member
    I want to upload a document
    So that it can be analyzed
"""
        result = parse_feature_content(content)
        assert result.persona == "Staff Member"
        assert result.i_want == "upload a document"


class TestParseFeatureFile:
    """Test parse_feature_file function."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project structure."""
        # Create feature directory structure
        feature_dir = tmp_path / "tests" / "e2e" / "my-app" / "features"
        feature_dir.mkdir(parents=True)
        return tmp_path

    def test_parse_feature_file_success(self, temp_project: Path) -> None:
        """Test parsing a feature file."""
        feature_dir = temp_project / "tests" / "e2e" / "my-app" / "features"
        feature_file = feature_dir / "submit.feature"
        feature_file.write_text("""Feature: Submit Form

  As a User
  I want to submit a form
  So that my data is saved

  Scenario: Valid submission
    Given I fill the form
    When I submit
    Then it succeeds
""")

        story = parse_feature_file(feature_file, temp_project)

        assert story is not None
        assert story.feature_title == "Submit Form"
        assert story.persona == "User"
        assert story.app_slug == "my-app"
        assert "tests/e2e/my-app/features/submit.feature" in story.file_path

    def test_parse_feature_file_with_explicit_app(self, temp_project: Path) -> None:
        """Test parsing with explicit app slug override."""
        feature_dir = temp_project / "tests" / "e2e" / "my-app" / "features"
        feature_file = feature_dir / "test.feature"
        feature_file.write_text("Feature: Test\n\n  As a User\n")

        story = parse_feature_file(feature_file, temp_project, app_slug="override-app")

        assert story is not None
        assert story.app_slug == "override-app"

    def test_parse_feature_file_nonexistent(self, temp_project: Path) -> None:
        """Test parsing a nonexistent file returns None."""
        nonexistent = temp_project / "nonexistent.feature"
        story = parse_feature_file(nonexistent, temp_project)
        assert story is None

    def test_parse_feature_file_outside_project_root(self, tmp_path: Path) -> None:
        """Test parsing a feature file outside the project root logs warning but works."""
        # Create feature file in tmp_path
        feature_file = tmp_path / "test.feature"
        feature_file.write_text("Feature: Test\n\n  As a User\n  I want to test\n")

        # Use a different directory as project root (feature is outside)
        project_root = tmp_path / "project"
        project_root.mkdir()

        story = parse_feature_file(feature_file, project_root)

        assert story is not None
        assert story.feature_title == "Test"
        # File path should be the full path when outside project root
        assert str(feature_file) in story.file_path or "test.feature" in story.file_path

    def test_parse_feature_file_unknown_app_slug_structure(self, tmp_path: Path) -> None:
        """Test parsing feature file with non-standard path defaults to 'unknown' app."""
        # Create a feature file not in tests/e2e/{app}/features/ structure
        feature_dir = tmp_path / "features"
        feature_dir.mkdir()
        feature_file = feature_dir / "test.feature"
        feature_file.write_text("Feature: Test\n\n  As a User\n  I want to test\n")

        story = parse_feature_file(feature_file, tmp_path)

        assert story is not None
        assert story.app_slug == "unknown"

    def test_parse_feature_file_short_path_defaults_to_unknown(self, tmp_path: Path) -> None:
        """Test parsing feature with path too short for app extraction defaults to 'unknown'."""
        # Create feature file directly in tmp_path (path has < 4 parts)
        feature_file = tmp_path / "test.feature"
        feature_file.write_text("Feature: Test\n\n  As a User\n  I want to test\n")

        story = parse_feature_file(feature_file, tmp_path)

        assert story is not None
        assert story.app_slug == "unknown"


class TestScanFeatureDirectory:
    """Test scan_feature_directory function."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project with multiple apps."""
        # Create app1 features
        app1_dir = tmp_path / "tests" / "e2e" / "app-one" / "features"
        app1_dir.mkdir(parents=True)
        (app1_dir / "feature1.feature").write_text(
            "Feature: Feature One\n\n  As a User\n  I want to do one\n"
        )
        (app1_dir / "feature2.feature").write_text(
            "Feature: Feature Two\n\n  As an Admin\n  I want to do two\n"
        )

        # Create app2 features
        app2_dir = tmp_path / "tests" / "e2e" / "app-two" / "features"
        app2_dir.mkdir(parents=True)
        (app2_dir / "feature3.feature").write_text(
            "Feature: Feature Three\n\n  As a Customer\n  I want to do three\n"
        )

        return tmp_path

    def test_scan_finds_all_features(self, temp_project: Path) -> None:
        """Test scanning finds all feature files."""
        feature_dir = temp_project / "tests" / "e2e"
        stories = scan_feature_directory(feature_dir, temp_project)

        assert len(stories) == 3
        titles = {s.feature_title for s in stories}
        assert titles == {"Feature One", "Feature Two", "Feature Three"}

    def test_scan_extracts_apps(self, temp_project: Path) -> None:
        """Test scanning correctly extracts app slugs."""
        feature_dir = temp_project / "tests" / "e2e"
        stories = scan_feature_directory(feature_dir, temp_project)

        apps = {s.app_slug for s in stories}
        assert apps == {"app-one", "app-two"}

    def test_scan_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test scanning nonexistent directory returns empty list."""
        stories = scan_feature_directory(tmp_path / "nonexistent", tmp_path)
        assert stories == []

    def test_scan_empty_directory(self, tmp_path: Path) -> None:
        """Test scanning empty directory returns empty list."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        stories = scan_feature_directory(empty_dir, tmp_path)
        assert stories == []
