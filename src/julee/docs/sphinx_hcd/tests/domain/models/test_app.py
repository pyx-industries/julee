"""Tests for App domain model."""

import pytest
from pydantic import ValidationError

from julee.docs.sphinx_hcd.domain.models.app import App, AppType


class TestAppType:
    """Test AppType enum."""

    def test_app_type_values(self) -> None:
        """Test AppType enum values."""
        assert AppType.STAFF.value == "staff"
        assert AppType.EXTERNAL.value == "external"
        assert AppType.MEMBER_TOOL.value == "member-tool"
        assert AppType.UNKNOWN.value == "unknown"

    def test_from_string_valid(self) -> None:
        """Test from_string with valid values."""
        assert AppType.from_string("staff") == AppType.STAFF
        assert AppType.from_string("external") == AppType.EXTERNAL
        assert AppType.from_string("member-tool") == AppType.MEMBER_TOOL

    def test_from_string_case_insensitive(self) -> None:
        """Test from_string is case-insensitive."""
        assert AppType.from_string("STAFF") == AppType.STAFF
        assert AppType.from_string("Staff") == AppType.STAFF

    def test_from_string_unknown(self) -> None:
        """Test from_string returns UNKNOWN for invalid values."""
        assert AppType.from_string("invalid") == AppType.UNKNOWN
        assert AppType.from_string("") == AppType.UNKNOWN


class TestAppCreation:
    """Test App model creation and validation."""

    def test_create_app_with_required_fields(self) -> None:
        """Test creating an app with minimum required fields."""
        app = App(
            slug="staff-portal",
            name="Staff Portal",
        )

        assert app.slug == "staff-portal"
        assert app.name == "Staff Portal"
        assert app.app_type == AppType.UNKNOWN
        assert app.status is None
        assert app.description == ""
        assert app.accelerators == []

    def test_create_app_with_all_fields(self) -> None:
        """Test creating an app with all fields."""
        app = App(
            slug="staff-portal",
            name="Staff Portal",
            app_type=AppType.STAFF,
            status="live",
            description="Portal for staff members",
            accelerators=["user-auth", "doc-upload"],
            manifest_path="/path/to/app.yaml",
        )

        assert app.slug == "staff-portal"
        assert app.name == "Staff Portal"
        assert app.app_type == AppType.STAFF
        assert app.status == "live"
        assert app.description == "Portal for staff members"
        assert app.accelerators == ["user-auth", "doc-upload"]
        assert app.manifest_path == "/path/to/app.yaml"

    def test_name_normalized_computed_automatically(self) -> None:
        """Test that name_normalized is computed from name."""
        app = App(
            slug="staff-portal",
            name="Staff Portal",
        )

        assert app.name_normalized == "staff portal"

    def test_empty_slug_raises_error(self) -> None:
        """Test that empty slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            App(
                slug="",
                name="Test App",
            )

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError, match="name cannot be empty"):
            App(
                slug="test-app",
                name="",
            )

    def test_whitespace_only_slug_raises_error(self) -> None:
        """Test that whitespace-only slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            App(
                slug="   ",
                name="Test App",
            )


class TestAppFromManifest:
    """Test App.from_manifest factory method."""

    def test_from_manifest_creates_app(self) -> None:
        """Test creating an app from manifest data."""
        manifest = {
            "name": "Staff Portal",
            "type": "staff",
            "status": "live",
            "description": "Portal for staff members",
            "accelerators": ["user-auth"],
        }

        app = App.from_manifest(
            slug="staff-portal",
            manifest=manifest,
            manifest_path="/apps/staff-portal/app.yaml",
        )

        assert app.slug == "staff-portal"
        assert app.name == "Staff Portal"
        assert app.app_type == AppType.STAFF
        assert app.status == "live"
        assert app.description == "Portal for staff members"
        assert app.accelerators == ["user-auth"]
        assert app.manifest_path == "/apps/staff-portal/app.yaml"

    def test_from_manifest_default_name(self) -> None:
        """Test default name from slug when not in manifest."""
        manifest = {}

        app = App.from_manifest(
            slug="staff-portal",
            manifest=manifest,
            manifest_path="/apps/staff-portal/app.yaml",
        )

        assert app.name == "Staff Portal"

    def test_from_manifest_default_type(self) -> None:
        """Test default type when not in manifest."""
        manifest = {"name": "Test App"}

        app = App.from_manifest(
            slug="test-app",
            manifest=manifest,
            manifest_path="/apps/test-app/app.yaml",
        )

        assert app.app_type == AppType.UNKNOWN

    def test_from_manifest_strips_description(self) -> None:
        """Test that description whitespace is stripped."""
        manifest = {
            "name": "Test App",
            "description": "  Some description  \n",
        }

        app = App.from_manifest(
            slug="test-app",
            manifest=manifest,
            manifest_path="/apps/test-app/app.yaml",
        )

        assert app.description == "Some description"


class TestAppMatching:
    """Test App matching methods."""

    @pytest.fixture
    def sample_app(self) -> App:
        """Create a sample app for testing."""
        return App(
            slug="staff-portal",
            name="Staff Portal",
            app_type=AppType.STAFF,
        )

    def test_matches_type_with_enum(self, sample_app: App) -> None:
        """Test type matching with AppType enum."""
        assert sample_app.matches_type(AppType.STAFF) is True
        assert sample_app.matches_type(AppType.EXTERNAL) is False

    def test_matches_type_with_string(self, sample_app: App) -> None:
        """Test type matching with string."""
        assert sample_app.matches_type("staff") is True
        assert sample_app.matches_type("external") is False

    def test_matches_name_exact(self, sample_app: App) -> None:
        """Test name matching with exact name."""
        assert sample_app.matches_name("Staff Portal") is True

    def test_matches_name_case_insensitive(self, sample_app: App) -> None:
        """Test name matching is case-insensitive."""
        assert sample_app.matches_name("staff portal") is True
        assert sample_app.matches_name("STAFF PORTAL") is True

    def test_matches_name_no_match(self, sample_app: App) -> None:
        """Test name matching returns False for non-match."""
        assert sample_app.matches_name("External App") is False


class TestAppTypeLabel:
    """Test App type_label property."""

    def test_type_label_staff(self) -> None:
        """Test type label for staff app."""
        app = App(slug="test", name="Test", app_type=AppType.STAFF)
        assert app.type_label == "Staff Application"

    def test_type_label_external(self) -> None:
        """Test type label for external app."""
        app = App(slug="test", name="Test", app_type=AppType.EXTERNAL)
        assert app.type_label == "External Application"

    def test_type_label_member_tool(self) -> None:
        """Test type label for member tool."""
        app = App(slug="test", name="Test", app_type=AppType.MEMBER_TOOL)
        assert app.type_label == "Member Tool"

    def test_type_label_unknown(self) -> None:
        """Test type label for unknown type."""
        app = App(slug="test", name="Test", app_type=AppType.UNKNOWN)
        assert app.type_label == "Unknown"


class TestAppSerialization:
    """Test App serialization."""

    def test_app_to_dict(self) -> None:
        """Test app can be serialized to dict."""
        app = App(
            slug="test-app",
            name="Test App",
            app_type=AppType.STAFF,
        )

        data = app.model_dump()
        assert data["slug"] == "test-app"
        assert data["name"] == "Test App"
        assert data["app_type"] == AppType.STAFF

    def test_app_to_json(self) -> None:
        """Test app can be serialized to JSON."""
        app = App(
            slug="test-app",
            name="Test App",
        )

        json_str = app.model_dump_json()
        assert '"slug":"test-app"' in json_str
