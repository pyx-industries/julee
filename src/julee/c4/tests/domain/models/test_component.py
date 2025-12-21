"""Tests for Component domain model."""

import pytest
from pydantic import ValidationError

from julee.c4.domain.models.component import Component


class TestComponentCreation:
    """Test Component model creation and validation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating a component with minimum required fields."""
        component = Component(
            slug="auth-controller",
            name="Authentication Controller",
            container_slug="api-app",
            system_slug="banking-system",
        )

        assert component.slug == "auth-controller"
        assert component.name == "Authentication Controller"
        assert component.container_slug == "api-app"
        assert component.system_slug == "banking-system"
        assert component.description == ""
        assert component.tags == []

    def test_create_with_all_fields(self) -> None:
        """Test creating a component with all fields."""
        component = Component(
            slug="auth-controller",
            name="Authentication Controller",
            container_slug="api-app",
            system_slug="banking-system",
            description="Handles user authentication and authorization",
            technology="Python, FastAPI",
            interface="REST API",
            code_path="src/controllers/auth.py",
            url="https://docs.example.com/auth",
            tags=["security", "core"],
            docname="architecture/components",
        )

        assert component.description == "Handles user authentication and authorization"
        assert component.technology == "Python, FastAPI"
        assert component.interface == "REST API"
        assert component.code_path == "src/controllers/auth.py"

    def test_empty_slug_raises_error(self) -> None:
        """Test that empty slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            Component(
                slug="",
                name="Test",
                container_slug="container",
                system_slug="system",
            )

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError, match="name cannot be empty"):
            Component(
                slug="test",
                name="",
                container_slug="container",
                system_slug="system",
            )

    def test_empty_container_slug_raises_error(self) -> None:
        """Test that empty container_slug raises validation error."""
        with pytest.raises(ValidationError, match="container_slug cannot be empty"):
            Component(
                slug="test",
                name="Test",
                container_slug="",
                system_slug="system",
            )

    def test_empty_system_slug_raises_error(self) -> None:
        """Test that empty system_slug raises validation error."""
        with pytest.raises(ValidationError, match="system_slug cannot be empty"):
            Component(
                slug="test",
                name="Test",
                container_slug="container",
                system_slug="",
            )

    def test_slug_is_normalized(self) -> None:
        """Test that slug is normalized (slugified)."""
        component = Component(
            slug="Auth Controller",
            name="Test",
            container_slug="container",
            system_slug="system",
        )
        assert component.slug == "auth-controller"


class TestComponentComputedFields:
    """Test computed fields and properties."""

    def test_name_normalized(self) -> None:
        """Test normalized name is computed."""
        component = Component(
            slug="test",
            name="Authentication Controller",
            container_slug="container",
            system_slug="system",
        )
        assert component.name_normalized == "authentication controller"

    def test_qualified_slug(self) -> None:
        """Test qualified slug includes container and system."""
        component = Component(
            slug="auth-controller",
            name="Test",
            container_slug="api-app",
            system_slug="banking-system",
        )
        assert component.qualified_slug == "banking-system/api-app/auth-controller"


class TestComponentTags:
    """Test tag operations."""

    def test_has_tag_exact(self) -> None:
        """Test tag lookup with exact match."""
        component = Component(
            slug="test",
            name="Test",
            container_slug="container",
            system_slug="system",
            tags=["security", "core"],
        )
        assert component.has_tag("security") is True
        assert component.has_tag("missing") is False

    def test_has_tag_case_insensitive(self) -> None:
        """Test tag lookup is case-insensitive."""
        component = Component(
            slug="test",
            name="Test",
            container_slug="container",
            system_slug="system",
            tags=["Security"],
        )
        assert component.has_tag("security") is True
        assert component.has_tag("SECURITY") is True

    def test_add_tag(self) -> None:
        """Test adding a new tag."""
        component = Component(
            slug="test",
            name="Test",
            container_slug="container",
            system_slug="system",
            tags=["existing"],
        )
        component.add_tag("new")
        assert "new" in component.tags
        assert len(component.tags) == 2


class TestComponentSerialization:
    """Test serialization."""

    def test_to_dict(self) -> None:
        """Test model can be serialized to dict."""
        component = Component(
            slug="test",
            name="Test Component",
            container_slug="container",
            system_slug="system",
            technology="Python",
        )
        data = component.model_dump()
        assert data["slug"] == "test"
        assert data["name"] == "Test Component"
        assert data["container_slug"] == "container"
        assert data["technology"] == "Python"
