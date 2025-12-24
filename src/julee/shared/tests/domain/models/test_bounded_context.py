"""Tests for BoundedContext and StructuralMarkers entities."""

import pytest

from julee.shared.entities import BoundedContext, StructuralMarkers


class TestStructuralMarkers:
    """Tests for StructuralMarkers entity."""

    def test_default_markers_all_false(self):
        """Default markers should all be False."""
        markers = StructuralMarkers()

        assert markers.has_domain_models is False
        assert markers.has_domain_repositories is False
        assert markers.has_domain_services is False
        assert markers.has_domain_use_cases is False
        assert markers.has_tests is False
        assert markers.has_parsers is False
        assert markers.has_serializers is False

    def test_has_clean_architecture_layers_with_models(self):
        """Should return True when has_domain_models is True."""
        markers = StructuralMarkers(has_domain_models=True)
        assert markers.has_clean_architecture_layers is True

    def test_has_clean_architecture_layers_with_use_cases(self):
        """Should return True when has_domain_use_cases is True."""
        markers = StructuralMarkers(has_domain_use_cases=True)
        assert markers.has_clean_architecture_layers is True

    def test_has_clean_architecture_layers_with_both(self):
        """Should return True when both models and use_cases present."""
        markers = StructuralMarkers(
            has_domain_models=True,
            has_domain_use_cases=True,
        )
        assert markers.has_clean_architecture_layers is True

    def test_has_clean_architecture_layers_without_models_or_use_cases(self):
        """Should return False when neither models nor use_cases present."""
        markers = StructuralMarkers(
            has_domain_repositories=True,
            has_domain_services=True,
        )
        assert markers.has_clean_architecture_layers is False


class TestBoundedContext:
    """Tests for BoundedContext entity."""

    def test_slug_validation_rejects_empty(self):
        """Should reject empty slug."""
        with pytest.raises(ValueError, match="slug cannot be empty"):
            BoundedContext(slug="", path="/some/path")

    def test_slug_validation_rejects_whitespace_only(self):
        """Should reject whitespace-only slug."""
        with pytest.raises(ValueError, match="slug cannot be empty"):
            BoundedContext(slug="   ", path="/some/path")

    def test_slug_validation_strips_whitespace(self):
        """Should strip whitespace from slug."""
        ctx = BoundedContext(slug="  hcd  ", path="/some/path")
        assert ctx.slug == "hcd"

    def test_import_path_extracts_from_src(self):
        """Should extract import path from src/ prefix."""
        ctx = BoundedContext(
            slug="hcd",
            path="/Users/chris/src/pyx/julee2/src/julee/hcd",
        )
        assert ctx.import_path == "julee.hcd"

    def test_import_path_handles_contrib(self):
        """Should handle contrib paths."""
        ctx = BoundedContext(
            slug="polling",
            path="/Users/chris/src/pyx/julee2/src/julee/contrib/polling",
        )
        assert ctx.import_path == "julee.contrib.polling"

    def test_import_path_without_src(self):
        """Should use full path when no src/ present."""
        ctx = BoundedContext(slug="hcd", path="/julee/hcd")
        assert ctx.import_path == "julee.hcd"

    def test_display_name_converts_slug(self):
        """Should convert slug to title case."""
        ctx = BoundedContext(slug="my-bounded-context", path="/path")
        assert ctx.display_name == "My Bounded Context"

    def test_display_name_handles_underscores(self):
        """Should convert underscores to spaces."""
        ctx = BoundedContext(slug="my_bounded_context", path="/path")
        assert ctx.display_name == "My Bounded Context"

    def test_absolute_path_returns_path_object(self):
        """Should return path as Path object."""
        ctx = BoundedContext(slug="hcd", path="/some/path")
        assert ctx.absolute_path.name == "path"

    def test_has_layer_models(self):
        """Should detect models layer."""
        ctx = BoundedContext(
            slug="hcd",
            path="/path",
            markers=StructuralMarkers(has_domain_models=True),
        )
        assert ctx.has_layer("models") is True
        assert ctx.has_layer("repositories") is False

    def test_has_layer_repositories(self):
        """Should detect repositories layer."""
        ctx = BoundedContext(
            slug="hcd",
            path="/path",
            markers=StructuralMarkers(has_domain_repositories=True),
        )
        assert ctx.has_layer("repositories") is True
        assert ctx.has_layer("models") is False

    def test_has_layer_services(self):
        """Should detect services layer."""
        ctx = BoundedContext(
            slug="hcd",
            path="/path",
            markers=StructuralMarkers(has_domain_services=True),
        )
        assert ctx.has_layer("services") is True

    def test_has_layer_use_cases(self):
        """Should detect use_cases layer."""
        ctx = BoundedContext(
            slug="hcd",
            path="/path",
            markers=StructuralMarkers(has_domain_use_cases=True),
        )
        assert ctx.has_layer("use_cases") is True

    def test_has_layer_unknown_returns_false(self):
        """Should return False for unknown layer."""
        ctx = BoundedContext(slug="hcd", path="/path")
        assert ctx.has_layer("unknown") is False

    def test_default_classification_flags(self):
        """Default classification flags should be False."""
        ctx = BoundedContext(slug="hcd", path="/path")
        assert ctx.is_contrib is False
        assert ctx.is_viewpoint is False

    def test_classification_flags_can_be_set(self):
        """Classification flags should be settable."""
        ctx = BoundedContext(
            slug="hcd",
            path="/path",
            is_contrib=True,
            is_viewpoint=True,
        )
        assert ctx.is_contrib is True
        assert ctx.is_viewpoint is True
