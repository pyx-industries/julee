"""Tests for YAML manifest parser."""

from pathlib import Path

import pytest

from julee.hcd.domain.models.app import AppType
from julee.hcd.domain.models.integration import Direction
from julee.hcd.parsers.yaml import (
    parse_app_manifest,
    parse_integration_manifest,
    parse_manifest_content,
    scan_app_manifests,
    scan_integration_manifests,
)


class TestParseManifestContent:
    """Test parse_manifest_content function."""

    def test_parse_valid_yaml(self) -> None:
        """Test parsing valid YAML content."""
        content = """
name: Staff Portal
type: staff
status: live
description: Portal for staff members
accelerators:
  - user-auth
  - doc-upload
"""
        result = parse_manifest_content(content)
        assert result is not None
        assert result["name"] == "Staff Portal"
        assert result["type"] == "staff"
        assert result["status"] == "live"
        assert result["accelerators"] == ["user-auth", "doc-upload"]

    def test_parse_empty_content(self) -> None:
        """Test parsing empty content."""
        result = parse_manifest_content("")
        assert result is None

    def test_parse_invalid_yaml(self) -> None:
        """Test parsing invalid YAML."""
        content = """
name: Test
invalid yaml: [unclosed bracket
"""
        result = parse_manifest_content(content)
        assert result is None

    def test_parse_minimal_yaml(self) -> None:
        """Test parsing minimal YAML."""
        content = "name: Test App"
        result = parse_manifest_content(content)
        assert result is not None
        assert result["name"] == "Test App"


class TestParseAppManifest:
    """Test parse_app_manifest function."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project structure."""
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()
        return tmp_path

    def test_parse_complete_manifest(self, temp_project: Path) -> None:
        """Test parsing a complete app manifest."""
        app_dir = temp_project / "apps" / "staff-portal"
        app_dir.mkdir(parents=True)
        manifest = app_dir / "app.yaml"
        manifest.write_text(
            """
name: Staff Portal
type: staff
status: live
description: Portal for staff members
accelerators:
  - user-auth
"""
        )

        app = parse_app_manifest(manifest)

        assert app is not None
        assert app.slug == "staff-portal"
        assert app.name == "Staff Portal"
        assert app.app_type == AppType.STAFF
        assert app.status == "live"
        assert app.accelerators == ["user-auth"]

    def test_parse_manifest_with_explicit_slug(self, temp_project: Path) -> None:
        """Test parsing with explicit app slug override."""
        app_dir = temp_project / "apps" / "original-slug"
        app_dir.mkdir(parents=True)
        manifest = app_dir / "app.yaml"
        manifest.write_text("name: Test App")

        app = parse_app_manifest(manifest, app_slug="override-slug")

        assert app is not None
        assert app.slug == "override-slug"

    def test_parse_manifest_default_name(self, temp_project: Path) -> None:
        """Test default name generated from slug."""
        app_dir = temp_project / "apps" / "my-cool-app"
        app_dir.mkdir(parents=True)
        manifest = app_dir / "app.yaml"
        manifest.write_text("type: staff")

        app = parse_app_manifest(manifest)

        assert app is not None
        assert app.name == "My Cool App"

    def test_parse_manifest_nonexistent(self, temp_project: Path) -> None:
        """Test parsing a nonexistent file returns None."""
        nonexistent = temp_project / "apps" / "nonexistent" / "app.yaml"
        app = parse_app_manifest(nonexistent)
        assert app is None

    def test_parse_manifest_empty_file(self, temp_project: Path) -> None:
        """Test parsing an empty manifest file."""
        app_dir = temp_project / "apps" / "empty-app"
        app_dir.mkdir(parents=True)
        manifest = app_dir / "app.yaml"
        manifest.write_text("")

        app = parse_app_manifest(manifest)
        assert app is None

    def test_parse_manifest_invalid_yaml(self, temp_project: Path) -> None:
        """Test parsing invalid YAML returns None."""
        app_dir = temp_project / "apps" / "bad-app"
        app_dir.mkdir(parents=True)
        manifest = app_dir / "app.yaml"
        manifest.write_text("invalid: [unclosed")

        app = parse_app_manifest(manifest)
        assert app is None


class TestScanAppManifests:
    """Test scan_app_manifests function."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project with multiple apps."""
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()

        # Create app1
        app1_dir = apps_dir / "staff-portal"
        app1_dir.mkdir()
        (app1_dir / "app.yaml").write_text(
            """
name: Staff Portal
type: staff
"""
        )

        # Create app2
        app2_dir = apps_dir / "customer-portal"
        app2_dir.mkdir()
        (app2_dir / "app.yaml").write_text(
            """
name: Customer Portal
type: external
"""
        )

        # Create app3 (member tool)
        app3_dir = apps_dir / "member-tool"
        app3_dir.mkdir()
        (app3_dir / "app.yaml").write_text(
            """
name: Member Tool
type: member-tool
"""
        )

        return tmp_path

    def test_scan_finds_all_apps(self, temp_project: Path) -> None:
        """Test scanning finds all app manifests."""
        apps_dir = temp_project / "apps"
        apps = scan_app_manifests(apps_dir)

        assert len(apps) == 3
        slugs = {a.slug for a in apps}
        assert slugs == {"staff-portal", "customer-portal", "member-tool"}

    def test_scan_extracts_types(self, temp_project: Path) -> None:
        """Test scanning correctly extracts app types."""
        apps_dir = temp_project / "apps"
        apps = scan_app_manifests(apps_dir)

        types_by_slug = {a.slug: a.app_type for a in apps}
        assert types_by_slug["staff-portal"] == AppType.STAFF
        assert types_by_slug["customer-portal"] == AppType.EXTERNAL
        assert types_by_slug["member-tool"] == AppType.MEMBER_TOOL

    def test_scan_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test scanning nonexistent directory returns empty list."""
        apps = scan_app_manifests(tmp_path / "nonexistent")
        assert apps == []

    def test_scan_empty_directory(self, tmp_path: Path) -> None:
        """Test scanning empty directory returns empty list."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        apps = scan_app_manifests(empty_dir)
        assert apps == []

    def test_scan_ignores_files_in_root(self, tmp_path: Path) -> None:
        """Test scanning ignores non-directory items."""
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()

        # Create a file in the apps dir (should be ignored)
        (apps_dir / "README.md").write_text("readme")

        # Create a valid app
        app_dir = apps_dir / "test-app"
        app_dir.mkdir()
        (app_dir / "app.yaml").write_text("name: Test App")

        apps = scan_app_manifests(apps_dir)
        assert len(apps) == 1
        assert apps[0].slug == "test-app"

    def test_scan_skips_directories_without_manifest(self, tmp_path: Path) -> None:
        """Test scanning skips directories without app.yaml."""
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()

        # Create directory without manifest
        (apps_dir / "no-manifest").mkdir()

        # Create valid app
        app_dir = apps_dir / "valid-app"
        app_dir.mkdir()
        (app_dir / "app.yaml").write_text("name: Valid App")

        apps = scan_app_manifests(apps_dir)
        assert len(apps) == 1
        assert apps[0].slug == "valid-app"


# Integration manifest parsing tests


class TestParseIntegrationManifest:
    """Test parse_integration_manifest function."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project structure."""
        integrations_dir = tmp_path / "integrations"
        integrations_dir.mkdir()
        return tmp_path

    def test_parse_complete_manifest(self, temp_project: Path) -> None:
        """Test parsing a complete integration manifest."""
        int_dir = temp_project / "integrations" / "pilot_data_collection"
        int_dir.mkdir(parents=True)
        manifest = int_dir / "integration.yaml"
        manifest.write_text(
            """
slug: pilot-data
name: Pilot Data Collection
description: Collects pilot data from external systems
direction: inbound
depends_on:
  - name: Pilot API
    url: https://pilot.example.com
  - name: Data Lake
"""
        )

        integration = parse_integration_manifest(manifest)

        assert integration is not None
        assert integration.slug == "pilot-data"
        assert integration.module == "pilot_data_collection"
        assert integration.name == "Pilot Data Collection"
        assert integration.direction == Direction.INBOUND
        assert len(integration.depends_on) == 2
        assert integration.depends_on[0].name == "Pilot API"
        assert integration.depends_on[0].url == "https://pilot.example.com"

    def test_parse_manifest_with_explicit_module(self, temp_project: Path) -> None:
        """Test parsing with explicit module name override."""
        int_dir = temp_project / "integrations" / "original_module"
        int_dir.mkdir(parents=True)
        manifest = int_dir / "integration.yaml"
        manifest.write_text("name: Test Integration")

        integration = parse_integration_manifest(
            manifest, module_name="override_module"
        )

        assert integration is not None
        assert integration.module == "override_module"

    def test_parse_manifest_default_slug(self, temp_project: Path) -> None:
        """Test default slug from module name."""
        int_dir = temp_project / "integrations" / "my_integration"
        int_dir.mkdir(parents=True)
        manifest = int_dir / "integration.yaml"
        manifest.write_text("name: My Integration")

        integration = parse_integration_manifest(manifest)

        assert integration is not None
        assert integration.slug == "my-integration"

    def test_parse_manifest_default_name(self, temp_project: Path) -> None:
        """Test default name from slug."""
        int_dir = temp_project / "integrations" / "data_sync"
        int_dir.mkdir(parents=True)
        manifest = int_dir / "integration.yaml"
        manifest.write_text("direction: outbound")

        integration = parse_integration_manifest(manifest)

        assert integration is not None
        assert integration.name == "Data Sync"

    def test_parse_manifest_default_direction(self, temp_project: Path) -> None:
        """Test default direction is bidirectional."""
        int_dir = temp_project / "integrations" / "test"
        int_dir.mkdir(parents=True)
        manifest = int_dir / "integration.yaml"
        manifest.write_text("name: Test")

        integration = parse_integration_manifest(manifest)

        assert integration is not None
        assert integration.direction == Direction.BIDIRECTIONAL

    def test_parse_manifest_nonexistent(self, temp_project: Path) -> None:
        """Test parsing a nonexistent file returns None."""
        nonexistent = temp_project / "integrations" / "nonexistent" / "integration.yaml"
        integration = parse_integration_manifest(nonexistent)
        assert integration is None

    def test_parse_manifest_empty_file(self, temp_project: Path) -> None:
        """Test parsing an empty manifest file."""
        int_dir = temp_project / "integrations" / "empty"
        int_dir.mkdir(parents=True)
        manifest = int_dir / "integration.yaml"
        manifest.write_text("")

        integration = parse_integration_manifest(manifest)
        assert integration is None

    def test_parse_manifest_invalid_yaml(self, temp_project: Path) -> None:
        """Test parsing invalid YAML returns None."""
        int_dir = temp_project / "integrations" / "bad"
        int_dir.mkdir(parents=True)
        manifest = int_dir / "integration.yaml"
        manifest.write_text("invalid: [unclosed")

        integration = parse_integration_manifest(manifest)
        assert integration is None


class TestScanIntegrationManifests:
    """Test scan_integration_manifests function."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project with multiple integrations."""
        integrations_dir = tmp_path / "integrations"
        integrations_dir.mkdir()

        # Create inbound integration
        int1_dir = integrations_dir / "pilot_data"
        int1_dir.mkdir()
        (int1_dir / "integration.yaml").write_text(
            """
name: Pilot Data
direction: inbound
"""
        )

        # Create outbound integration
        int2_dir = integrations_dir / "analytics_export"
        int2_dir.mkdir()
        (int2_dir / "integration.yaml").write_text(
            """
name: Analytics Export
direction: outbound
"""
        )

        # Create bidirectional integration
        int3_dir = integrations_dir / "data_sync"
        int3_dir.mkdir()
        (int3_dir / "integration.yaml").write_text(
            """
name: Data Sync
direction: bidirectional
"""
        )

        return tmp_path

    def test_scan_finds_all_integrations(self, temp_project: Path) -> None:
        """Test scanning finds all integration manifests."""
        integrations_dir = temp_project / "integrations"
        integrations = scan_integration_manifests(integrations_dir)

        assert len(integrations) == 3
        slugs = {i.slug for i in integrations}
        assert slugs == {"pilot-data", "analytics-export", "data-sync"}

    def test_scan_extracts_directions(self, temp_project: Path) -> None:
        """Test scanning correctly extracts directions."""
        integrations_dir = temp_project / "integrations"
        integrations = scan_integration_manifests(integrations_dir)

        directions_by_slug = {i.slug: i.direction for i in integrations}
        assert directions_by_slug["pilot-data"] == Direction.INBOUND
        assert directions_by_slug["analytics-export"] == Direction.OUTBOUND
        assert directions_by_slug["data-sync"] == Direction.BIDIRECTIONAL

    def test_scan_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test scanning nonexistent directory returns empty list."""
        integrations = scan_integration_manifests(tmp_path / "nonexistent")
        assert integrations == []

    def test_scan_empty_directory(self, tmp_path: Path) -> None:
        """Test scanning empty directory returns empty list."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        integrations = scan_integration_manifests(empty_dir)
        assert integrations == []

    def test_scan_ignores_underscore_directories(self, tmp_path: Path) -> None:
        """Test scanning ignores directories starting with underscore."""
        integrations_dir = tmp_path / "integrations"
        integrations_dir.mkdir()

        # Create ignored directory
        ignored_dir = integrations_dir / "_base"
        ignored_dir.mkdir()
        (ignored_dir / "integration.yaml").write_text("name: Base")

        # Create valid integration
        int_dir = integrations_dir / "valid"
        int_dir.mkdir()
        (int_dir / "integration.yaml").write_text("name: Valid")

        integrations = scan_integration_manifests(integrations_dir)
        assert len(integrations) == 1
        assert integrations[0].slug == "valid"

    def test_scan_ignores_files_in_root(self, tmp_path: Path) -> None:
        """Test scanning ignores non-directory items."""
        integrations_dir = tmp_path / "integrations"
        integrations_dir.mkdir()

        # Create a file in the integrations dir (should be ignored)
        (integrations_dir / "README.md").write_text("readme")

        # Create valid integration
        int_dir = integrations_dir / "test"
        int_dir.mkdir()
        (int_dir / "integration.yaml").write_text("name: Test")

        integrations = scan_integration_manifests(integrations_dir)
        assert len(integrations) == 1
        assert integrations[0].slug == "test"

    def test_scan_skips_directories_without_manifest(self, tmp_path: Path) -> None:
        """Test scanning skips directories without integration.yaml."""
        integrations_dir = tmp_path / "integrations"
        integrations_dir.mkdir()

        # Create directory without manifest
        (integrations_dir / "no_manifest").mkdir()

        # Create valid integration
        int_dir = integrations_dir / "valid"
        int_dir.mkdir()
        (int_dir / "integration.yaml").write_text("name: Valid")

        integrations = scan_integration_manifests(integrations_dir)
        assert len(integrations) == 1
        assert integrations[0].slug == "valid"
