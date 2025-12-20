"""Tests for story migration script."""

from pathlib import Path

from julee.docs.sphinx_hcd.scripts.migrate_stories import main, migrate_stories


class TestMigrateStories:
    """Tests for migrate_stories function."""

    def test_empty_directory_returns_zero_stories(self, tmp_path: Path):
        """Empty feature directory returns zero stories."""
        feature_dir = tmp_path / "features"
        feature_dir.mkdir()
        output_dir = tmp_path / "output"

        stats = migrate_stories(
            feature_dir=feature_dir,
            output_dir=output_dir,
            project_root=tmp_path,
            dry_run=True,
        )

        assert stats["stories_found"] == 0
        assert stats["files_written"] == 0

    def test_parses_feature_file_and_creates_rst(self, tmp_path: Path):
        """Feature file is parsed and RST file is created."""
        feature_dir = tmp_path / "tests" / "e2e" / "curator" / "features"
        feature_dir.mkdir(parents=True)
        output_dir = tmp_path / "docs" / "stories"

        # Create a sample feature file
        feature_content = """\
Feature: Upload Document

  As a Knowledge Curator
  I want to upload reference materials
  So that I can build the knowledge base

  Scenario: Upload PDF
    Given I am on the upload page
    When I select a PDF file
    Then the document is processed
"""
        (feature_dir / "upload_document.feature").write_text(feature_content)

        # Run migration (execute mode)
        stats = migrate_stories(
            feature_dir=tmp_path / "tests" / "e2e",
            output_dir=output_dir,
            project_root=tmp_path,
            dry_run=False,
        )

        assert stats["stories_found"] == 1
        assert stats["files_written"] == 1

        # Verify RST file exists
        rst_files = list(output_dir.glob("*.rst"))
        assert len(rst_files) == 1

        # Verify content
        rst_content = rst_files[0].read_text()
        assert "define-story::" in rst_content
        assert "Upload Document" in rst_content
        assert "Knowledge Curator" in rst_content

    def test_dry_run_does_not_write_files(self, tmp_path: Path):
        """Dry run mode does not create output files."""
        feature_dir = tmp_path / "tests" / "e2e" / "app" / "features"
        feature_dir.mkdir(parents=True)
        output_dir = tmp_path / "docs" / "stories"

        feature_content = """\
Feature: Test Feature

  As a User
  I want to test something
  So that it works
"""
        (feature_dir / "test.feature").write_text(feature_content)

        stats = migrate_stories(
            feature_dir=tmp_path / "tests" / "e2e",
            output_dir=output_dir,
            project_root=tmp_path,
            dry_run=True,
        )

        assert stats["stories_found"] == 1
        assert stats["files_written"] == 0
        assert not output_dir.exists()

    def test_skips_existing_files(self, tmp_path: Path):
        """Existing RST files are skipped."""
        feature_dir = tmp_path / "tests" / "e2e" / "myapp" / "features"
        feature_dir.mkdir(parents=True)
        output_dir = tmp_path / "docs" / "stories"
        output_dir.mkdir(parents=True)

        feature_content = """\
Feature: Existing Feature

  As a User
  I want to test
  So that it works
"""
        (feature_dir / "existing.feature").write_text(feature_content)

        # Pre-create the output file
        (output_dir / "myapp--existing-feature.rst").write_text("existing content")

        stats = migrate_stories(
            feature_dir=tmp_path / "tests" / "e2e",
            output_dir=output_dir,
            project_root=tmp_path,
            dry_run=False,
        )

        assert stats["stories_found"] == 1
        assert stats["files_written"] == 0
        assert stats["files_skipped"] == 1

        # Verify original content preserved
        content = (output_dir / "myapp--existing-feature.rst").read_text()
        assert content == "existing content"


class TestMainCLI:
    """Tests for CLI entry point."""

    def test_main_dry_run_succeeds(self, tmp_path: Path):
        """CLI dry run returns success."""
        feature_dir = tmp_path / "features"
        feature_dir.mkdir()
        output_dir = tmp_path / "output"

        result = main(
            [
                "--feature-dir",
                str(feature_dir),
                "--output-dir",
                str(output_dir),
                "--project-root",
                str(tmp_path),
            ]
        )

        assert result == 0

    def test_main_execute_creates_files(self, tmp_path: Path):
        """CLI execute mode creates files."""
        feature_dir = tmp_path / "tests" / "e2e" / "demo" / "features"
        feature_dir.mkdir(parents=True)
        output_dir = tmp_path / "output"

        (feature_dir / "demo.feature").write_text(
            """\
Feature: Demo Feature

  As a Demo User
  I want to demonstrate
  So that it works
"""
        )

        result = main(
            [
                "--feature-dir",
                str(tmp_path / "tests" / "e2e"),
                "--output-dir",
                str(output_dir),
                "--project-root",
                str(tmp_path),
                "--execute",
            ]
        )

        assert result == 0
        assert output_dir.exists()
        assert len(list(output_dir.glob("*.rst"))) == 1
