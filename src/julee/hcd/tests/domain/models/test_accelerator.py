"""Tests for Accelerator domain model."""

import pytest
from pydantic import ValidationError

from julee.hcd.domain.models.accelerator import (
    Accelerator,
    IntegrationReference,
)


class TestIntegrationReference:
    """Test IntegrationReference model."""

    def test_create_with_slug_only(self) -> None:
        """Test creating with just slug."""
        ref = IntegrationReference(slug="pilot-data")
        assert ref.slug == "pilot-data"
        assert ref.description == ""

    def test_create_with_description(self) -> None:
        """Test creating with description."""
        ref = IntegrationReference(
            slug="pilot-data",
            description="Scheme documentation, standards materials",
        )
        assert ref.slug == "pilot-data"
        assert ref.description == "Scheme documentation, standards materials"

    def test_empty_slug_raises_error(self) -> None:
        """Test that empty slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            IntegrationReference(slug="")

    def test_from_dict_complete(self) -> None:
        """Test from_dict with full dict."""
        ref = IntegrationReference.from_dict(
            {
                "slug": "pilot-data",
                "description": "Test description",
            }
        )
        assert ref.slug == "pilot-data"
        assert ref.description == "Test description"

    def test_from_dict_string(self) -> None:
        """Test from_dict with plain string."""
        ref = IntegrationReference.from_dict("pilot-data")
        assert ref.slug == "pilot-data"
        assert ref.description == ""

    def test_from_dict_minimal(self) -> None:
        """Test from_dict with minimal dict."""
        ref = IntegrationReference.from_dict({"slug": "pilot-data"})
        assert ref.slug == "pilot-data"
        assert ref.description == ""


class TestAcceleratorCreation:
    """Test Accelerator model creation and validation."""

    def test_create_accelerator_minimal(self) -> None:
        """Test creating an accelerator with minimum fields."""
        accel = Accelerator(slug="vocabulary")
        assert accel.slug == "vocabulary"
        assert accel.status == ""
        assert accel.milestone is None
        assert accel.acceptance is None
        assert accel.objective == ""
        assert accel.sources_from == []
        assert accel.feeds_into == []
        assert accel.publishes_to == []
        assert accel.depends_on == []
        assert accel.docname == ""

    def test_create_accelerator_complete(self) -> None:
        """Test creating an accelerator with all fields."""
        accel = Accelerator(
            slug="vocabulary",
            status="alpha",
            milestone="2 (Nov 2025)",
            acceptance="Reference environment deployed and accepted.",
            objective="Accelerate the creation of Sustainable Vocabulary Catalogs.",
            sources_from=[
                IntegrationReference(
                    slug="pilot-data-collection",
                    description="Scheme documentation, standards materials",
                ),
            ],
            feeds_into=["traceability", "conformity"],
            publishes_to=[
                IntegrationReference(
                    slug="reference-implementation",
                    description="SVC artefacts",
                ),
            ],
            depends_on=["core-infrastructure"],
            docname="accelerators/vocabulary",
        )

        assert accel.slug == "vocabulary"
        assert accel.status == "alpha"
        assert accel.milestone == "2 (Nov 2025)"
        assert len(accel.sources_from) == 1
        assert accel.sources_from[0].slug == "pilot-data-collection"
        assert len(accel.feeds_into) == 2
        assert len(accel.publishes_to) == 1

    def test_empty_slug_raises_error(self) -> None:
        """Test that empty slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            Accelerator(slug="")

    def test_whitespace_slug_raises_error(self) -> None:
        """Test that whitespace-only slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            Accelerator(slug="   ")

    def test_slug_stripped(self) -> None:
        """Test that slug is stripped of whitespace."""
        accel = Accelerator(slug="  vocabulary  ")
        assert accel.slug == "vocabulary"


class TestAcceleratorProperties:
    """Test Accelerator properties."""

    def test_display_title(self) -> None:
        """Test display_title property."""
        accel = Accelerator(slug="vocabulary")
        assert accel.display_title == "Vocabulary"

    def test_display_title_multiple_words(self) -> None:
        """Test display_title with hyphens."""
        accel = Accelerator(slug="core-infrastructure")
        assert accel.display_title == "Core Infrastructure"

    def test_status_normalized(self) -> None:
        """Test status_normalized property."""
        accel = Accelerator(slug="test", status="Alpha")
        assert accel.status_normalized == "alpha"

    def test_status_normalized_empty(self) -> None:
        """Test status_normalized with empty status."""
        accel = Accelerator(slug="test")
        assert accel.status_normalized == ""


class TestAcceleratorDependencies:
    """Test Accelerator dependency methods."""

    @pytest.fixture
    def sample_accelerator(self) -> Accelerator:
        """Create a sample accelerator for testing."""
        return Accelerator(
            slug="vocabulary",
            sources_from=[
                IntegrationReference(slug="pilot-data", description="Pilot data"),
                IntegrationReference(slug="standards", description="Standards"),
            ],
            publishes_to=[
                IntegrationReference(slug="reference-impl", description="SVC"),
            ],
            feeds_into=["traceability", "conformity"],
            depends_on=["core-infrastructure"],
        )

    def test_has_integration_dependency_sources(
        self, sample_accelerator: Accelerator
    ) -> None:
        """Test checking sources_from dependency."""
        assert sample_accelerator.has_integration_dependency("pilot-data") is True
        assert sample_accelerator.has_integration_dependency("standards") is True

    def test_has_integration_dependency_publishes(
        self, sample_accelerator: Accelerator
    ) -> None:
        """Test checking publishes_to dependency."""
        assert sample_accelerator.has_integration_dependency("reference-impl") is True

    def test_has_integration_dependency_no_match(
        self, sample_accelerator: Accelerator
    ) -> None:
        """Test checking nonexistent dependency."""
        assert sample_accelerator.has_integration_dependency("unknown") is False

    def test_has_accelerator_dependency_depends(
        self, sample_accelerator: Accelerator
    ) -> None:
        """Test checking depends_on dependency."""
        assert (
            sample_accelerator.has_accelerator_dependency("core-infrastructure") is True
        )

    def test_has_accelerator_dependency_feeds(
        self, sample_accelerator: Accelerator
    ) -> None:
        """Test checking feeds_into dependency."""
        assert sample_accelerator.has_accelerator_dependency("traceability") is True
        assert sample_accelerator.has_accelerator_dependency("conformity") is True

    def test_has_accelerator_dependency_no_match(
        self, sample_accelerator: Accelerator
    ) -> None:
        """Test checking nonexistent accelerator dependency."""
        assert sample_accelerator.has_accelerator_dependency("unknown") is False

    def test_get_sources_from_slugs(self, sample_accelerator: Accelerator) -> None:
        """Test getting source integration slugs."""
        slugs = sample_accelerator.get_sources_from_slugs()
        assert slugs == ["pilot-data", "standards"]

    def test_get_publishes_to_slugs(self, sample_accelerator: Accelerator) -> None:
        """Test getting publish integration slugs."""
        slugs = sample_accelerator.get_publishes_to_slugs()
        assert slugs == ["reference-impl"]

    def test_get_integration_description_sources(
        self, sample_accelerator: Accelerator
    ) -> None:
        """Test getting description from sources_from."""
        desc = sample_accelerator.get_integration_description(
            "pilot-data", "sources_from"
        )
        assert desc == "Pilot data"

    def test_get_integration_description_publishes(
        self, sample_accelerator: Accelerator
    ) -> None:
        """Test getting description from publishes_to."""
        desc = sample_accelerator.get_integration_description(
            "reference-impl", "publishes_to"
        )
        assert desc == "SVC"

    def test_get_integration_description_not_found(
        self, sample_accelerator: Accelerator
    ) -> None:
        """Test getting description for nonexistent integration."""
        desc = sample_accelerator.get_integration_description("unknown", "sources_from")
        assert desc is None


class TestAcceleratorSerialization:
    """Test Accelerator serialization."""

    def test_accelerator_to_dict(self) -> None:
        """Test accelerator can be serialized to dict."""
        accel = Accelerator(
            slug="test",
            status="alpha",
            sources_from=[IntegrationReference(slug="pilot", description="Data")],
        )

        data = accel.model_dump()
        assert data["slug"] == "test"
        assert data["status"] == "alpha"
        assert len(data["sources_from"]) == 1
        assert data["sources_from"][0]["slug"] == "pilot"

    def test_accelerator_to_json(self) -> None:
        """Test accelerator can be serialized to JSON."""
        accel = Accelerator(slug="test", status="alpha")
        json_str = accel.model_dump_json()
        assert '"slug":"test"' in json_str
        assert '"status":"alpha"' in json_str
