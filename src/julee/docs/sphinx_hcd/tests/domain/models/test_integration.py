"""Tests for Integration domain model."""

import pytest
from pydantic import ValidationError

from julee.docs.sphinx_hcd.domain.models.integration import (
    Direction,
    ExternalDependency,
    Integration,
)


class TestDirection:
    """Test Direction enum."""

    def test_direction_values(self) -> None:
        """Test Direction enum values."""
        assert Direction.INBOUND.value == "inbound"
        assert Direction.OUTBOUND.value == "outbound"
        assert Direction.BIDIRECTIONAL.value == "bidirectional"

    def test_from_string_valid(self) -> None:
        """Test from_string with valid values."""
        assert Direction.from_string("inbound") == Direction.INBOUND
        assert Direction.from_string("outbound") == Direction.OUTBOUND
        assert Direction.from_string("bidirectional") == Direction.BIDIRECTIONAL

    def test_from_string_case_insensitive(self) -> None:
        """Test from_string is case-insensitive."""
        assert Direction.from_string("INBOUND") == Direction.INBOUND
        assert Direction.from_string("Outbound") == Direction.OUTBOUND

    def test_from_string_unknown(self) -> None:
        """Test from_string defaults to BIDIRECTIONAL for invalid values."""
        assert Direction.from_string("invalid") == Direction.BIDIRECTIONAL
        assert Direction.from_string("") == Direction.BIDIRECTIONAL

    def test_direction_labels(self) -> None:
        """Test direction label property."""
        assert Direction.INBOUND.label == "Inbound (data source)"
        assert Direction.OUTBOUND.label == "Outbound (data sink)"
        assert Direction.BIDIRECTIONAL.label == "Bidirectional"


class TestExternalDependency:
    """Test ExternalDependency model."""

    def test_create_with_name_only(self) -> None:
        """Test creating with just name."""
        dep = ExternalDependency(name="External API")
        assert dep.name == "External API"
        assert dep.url is None
        assert dep.description == ""

    def test_create_with_all_fields(self) -> None:
        """Test creating with all fields."""
        dep = ExternalDependency(
            name="External API",
            url="https://api.example.com",
            description="Third party API",
        )
        assert dep.name == "External API"
        assert dep.url == "https://api.example.com"
        assert dep.description == "Third party API"

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError, match="name cannot be empty"):
            ExternalDependency(name="")

    def test_from_dict_complete(self) -> None:
        """Test from_dict with complete data."""
        data = {
            "name": "External API",
            "url": "https://api.example.com",
            "description": "Third party API",
        }
        dep = ExternalDependency.from_dict(data)
        assert dep.name == "External API"
        assert dep.url == "https://api.example.com"

    def test_from_dict_minimal(self) -> None:
        """Test from_dict with minimal data."""
        data = {"name": "Simple API"}
        dep = ExternalDependency.from_dict(data)
        assert dep.name == "Simple API"
        assert dep.url is None


class TestIntegrationCreation:
    """Test Integration model creation and validation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating with minimum required fields."""
        integration = Integration(
            slug="data-sync",
            module="data_sync",
            name="Data Sync",
        )

        assert integration.slug == "data-sync"
        assert integration.module == "data_sync"
        assert integration.name == "Data Sync"
        assert integration.direction == Direction.BIDIRECTIONAL
        assert integration.depends_on == []

    def test_create_with_all_fields(self) -> None:
        """Test creating with all fields."""
        deps = [ExternalDependency(name="AWS S3", url="https://aws.amazon.com/s3")]
        integration = Integration(
            slug="data-sync",
            module="data_sync",
            name="Data Sync",
            description="Synchronizes data with external systems",
            direction=Direction.OUTBOUND,
            depends_on=deps,
            manifest_path="/path/to/integration.yaml",
        )

        assert integration.slug == "data-sync"
        assert integration.direction == Direction.OUTBOUND
        assert len(integration.depends_on) == 1
        assert integration.depends_on[0].name == "AWS S3"

    def test_name_normalized_computed(self) -> None:
        """Test that name_normalized is computed."""
        integration = Integration(
            slug="data-sync",
            module="data_sync",
            name="Data Sync Service",
        )
        assert integration.name_normalized == "data sync service"

    def test_empty_slug_raises_error(self) -> None:
        """Test that empty slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            Integration(slug="", module="test", name="Test")

    def test_empty_module_raises_error(self) -> None:
        """Test that empty module raises validation error."""
        with pytest.raises(ValidationError, match="module cannot be empty"):
            Integration(slug="test", module="", name="Test")

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError, match="name cannot be empty"):
            Integration(slug="test", module="test", name="")


class TestIntegrationFromManifest:
    """Test Integration.from_manifest factory method."""

    def test_from_manifest_complete(self) -> None:
        """Test creating from complete manifest."""
        manifest = {
            "slug": "pilot-data",
            "name": "Pilot Data Collection",
            "description": "Collects pilot data",
            "direction": "inbound",
            "depends_on": [
                {"name": "Pilot API", "url": "https://pilot.example.com"},
                {"name": "Data Lake"},
            ],
        }

        integration = Integration.from_manifest(
            module_name="pilot_data_collection",
            manifest=manifest,
            manifest_path="/integrations/pilot_data_collection/integration.yaml",
        )

        assert integration.slug == "pilot-data"
        assert integration.module == "pilot_data_collection"
        assert integration.name == "Pilot Data Collection"
        assert integration.direction == Direction.INBOUND
        assert len(integration.depends_on) == 2
        assert integration.depends_on[0].name == "Pilot API"
        assert integration.depends_on[0].url == "https://pilot.example.com"

    def test_from_manifest_default_slug(self) -> None:
        """Test default slug from module name."""
        manifest = {"name": "Test Integration"}

        integration = Integration.from_manifest(
            module_name="my_integration",
            manifest=manifest,
            manifest_path="/path/to/integration.yaml",
        )

        assert integration.slug == "my-integration"

    def test_from_manifest_default_name(self) -> None:
        """Test default name from slug."""
        manifest = {}

        integration = Integration.from_manifest(
            module_name="data_sync",
            manifest=manifest,
            manifest_path="/path/to/integration.yaml",
        )

        assert integration.name == "Data Sync"

    def test_from_manifest_default_direction(self) -> None:
        """Test default direction is bidirectional."""
        manifest = {"name": "Test"}

        integration = Integration.from_manifest(
            module_name="test",
            manifest=manifest,
            manifest_path="/path/to/integration.yaml",
        )

        assert integration.direction == Direction.BIDIRECTIONAL

    def test_from_manifest_string_dependency(self) -> None:
        """Test parsing simple string dependencies."""
        manifest = {
            "name": "Test",
            "depends_on": ["Simple Dep"],
        }

        integration = Integration.from_manifest(
            module_name="test",
            manifest=manifest,
            manifest_path="/path/to/integration.yaml",
        )

        assert len(integration.depends_on) == 1
        assert integration.depends_on[0].name == "Simple Dep"


class TestIntegrationMatching:
    """Test Integration matching methods."""

    @pytest.fixture
    def sample_integration(self) -> Integration:
        """Create a sample integration for testing."""
        return Integration(
            slug="data-sync",
            module="data_sync",
            name="Data Sync Service",
            direction=Direction.OUTBOUND,
            depends_on=[
                ExternalDependency(name="AWS S3"),
                ExternalDependency(name="External API"),
            ],
        )

    def test_matches_direction_with_enum(self, sample_integration: Integration) -> None:
        """Test direction matching with enum."""
        assert sample_integration.matches_direction(Direction.OUTBOUND) is True
        assert sample_integration.matches_direction(Direction.INBOUND) is False

    def test_matches_direction_with_string(
        self, sample_integration: Integration
    ) -> None:
        """Test direction matching with string."""
        assert sample_integration.matches_direction("outbound") is True
        assert sample_integration.matches_direction("inbound") is False

    def test_matches_name_exact(self, sample_integration: Integration) -> None:
        """Test name matching with exact name."""
        assert sample_integration.matches_name("Data Sync Service") is True

    def test_matches_name_case_insensitive(
        self, sample_integration: Integration
    ) -> None:
        """Test name matching is case-insensitive."""
        assert sample_integration.matches_name("data sync service") is True

    def test_has_dependency(self, sample_integration: Integration) -> None:
        """Test checking for dependency."""
        assert sample_integration.has_dependency("AWS S3") is True
        assert sample_integration.has_dependency("aws s3") is True
        assert sample_integration.has_dependency("Unknown") is False


class TestIntegrationProperties:
    """Test Integration properties."""

    def test_direction_label(self) -> None:
        """Test direction_label property."""
        integration = Integration(
            slug="test",
            module="test",
            name="Test",
            direction=Direction.INBOUND,
        )
        assert integration.direction_label == "Inbound (data source)"

    def test_module_path(self) -> None:
        """Test module_path property."""
        integration = Integration(
            slug="test",
            module="my_module",
            name="Test",
        )
        assert integration.module_path == "integrations.my_module"


class TestIntegrationSerialization:
    """Test Integration serialization."""

    def test_integration_to_dict(self) -> None:
        """Test integration can be serialized to dict."""
        integration = Integration(
            slug="test",
            module="test",
            name="Test",
            direction=Direction.INBOUND,
        )

        data = integration.model_dump()
        assert data["slug"] == "test"
        assert data["direction"] == Direction.INBOUND

    def test_integration_to_json(self) -> None:
        """Test integration can be serialized to JSON."""
        integration = Integration(
            slug="test",
            module="test",
            name="Test",
        )

        json_str = integration.model_dump_json()
        assert '"slug":"test"' in json_str
