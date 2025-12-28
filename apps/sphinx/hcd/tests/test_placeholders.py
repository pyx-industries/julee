"""Tests for placeholder infrastructure."""

import pytest
from docutils import nodes

from apps.sphinx.hcd.directives.placeholders import (
    HCDPlaceholder,
    PlaceholderRegistry,
    register_placeholder,
)


class SamplePlaceholder(HCDPlaceholder):
    """Sample placeholder for unit tests."""

    pass


class AnotherSamplePlaceholder(HCDPlaceholder):
    """Another sample placeholder."""

    pass


class TestHCDPlaceholder:
    """Test HCDPlaceholder base class."""

    def test_inherits_from_nodes(self) -> None:
        """Test placeholder inherits from docutils nodes."""
        placeholder = SamplePlaceholder()
        assert isinstance(placeholder, nodes.General)
        assert isinstance(placeholder, nodes.Element)

    def test_can_store_attributes(self) -> None:
        """Test placeholder can store attributes."""
        placeholder = SamplePlaceholder()
        placeholder["slug"] = "my-slug"
        placeholder["title"] = "My Title"

        assert placeholder["slug"] == "my-slug"
        assert placeholder["title"] == "My Title"


class TestPlaceholderRegistry:
    """Test PlaceholderRegistry class."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        PlaceholderRegistry.clear()

    def test_register_and_get_builder(self) -> None:
        """Test registering and retrieving a builder."""

        def my_builder(app, node, docname, context):
            return [nodes.paragraph(text="test")]

        PlaceholderRegistry.register(SamplePlaceholder, my_builder)

        builder = PlaceholderRegistry.get_builder(SamplePlaceholder)
        assert builder is my_builder

    def test_get_unregistered_returns_none(self) -> None:
        """Test getting unregistered placeholder returns None."""
        builder = PlaceholderRegistry.get_builder(SamplePlaceholder)
        assert builder is None

    def test_is_registered(self) -> None:
        """Test is_registered check."""
        assert not PlaceholderRegistry.is_registered(SamplePlaceholder)

        PlaceholderRegistry.register(SamplePlaceholder, lambda a, n, d, c: [])

        assert PlaceholderRegistry.is_registered(SamplePlaceholder)

    def test_unregister(self) -> None:
        """Test unregistering a placeholder."""
        PlaceholderRegistry.register(SamplePlaceholder, lambda a, n, d, c: [])
        assert PlaceholderRegistry.is_registered(SamplePlaceholder)

        PlaceholderRegistry.unregister(SamplePlaceholder)
        assert not PlaceholderRegistry.is_registered(SamplePlaceholder)

    def test_unregister_nonexistent_no_error(self) -> None:
        """Test unregistering non-existent placeholder doesn't error."""
        PlaceholderRegistry.unregister(SamplePlaceholder)  # Should not raise

    def test_clear(self) -> None:
        """Test clearing all registrations."""
        PlaceholderRegistry.register(SamplePlaceholder, lambda a, n, d, c: [])
        PlaceholderRegistry.register(AnotherSamplePlaceholder, lambda a, n, d, c: [])

        PlaceholderRegistry.clear()

        assert not PlaceholderRegistry.is_registered(SamplePlaceholder)
        assert not PlaceholderRegistry.is_registered(AnotherSamplePlaceholder)

    def test_registered_types(self) -> None:
        """Test getting list of registered types."""
        PlaceholderRegistry.register(SamplePlaceholder, lambda a, n, d, c: [])
        PlaceholderRegistry.register(AnotherSamplePlaceholder, lambda a, n, d, c: [])

        types = PlaceholderRegistry.registered_types()

        assert SamplePlaceholder in types
        assert AnotherSamplePlaceholder in types
        assert len(types) == 2


class TestRegisterPlaceholderDecorator:
    """Test register_placeholder decorator."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        PlaceholderRegistry.clear()

    def test_decorator_registers_function(self) -> None:
        """Test decorator registers the builder function."""

        @register_placeholder(SamplePlaceholder)
        def build_test(app, node, docname, context):
            return [nodes.paragraph(text="decorated")]

        assert PlaceholderRegistry.is_registered(SamplePlaceholder)
        builder = PlaceholderRegistry.get_builder(SamplePlaceholder)
        assert builder is build_test

    def test_decorator_returns_original_function(self) -> None:
        """Test decorator returns the original function."""

        @register_placeholder(SamplePlaceholder)
        def build_test(app, node, docname, context):
            return [nodes.paragraph(text="test")]

        # Function should still be callable
        result = build_test(None, None, None, None)
        assert len(result) == 1
