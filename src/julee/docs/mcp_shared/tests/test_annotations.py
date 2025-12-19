"""Tests for annotation factory functions."""

import pytest
from mcp.types import ToolAnnotations

from julee.docs.mcp_shared import (
    create_annotation,
    delete_annotation,
    diagram_annotation,
    read_only_annotation,
    update_annotation,
)


class TestReadOnlyAnnotation:
    """Tests for read_only_annotation factory."""

    def test_returns_tool_annotations(self):
        result = read_only_annotation()
        assert isinstance(result, ToolAnnotations)

    def test_title_is_set(self):
        result = read_only_annotation("List Stories")
        assert result.title == "List Stories"

    def test_title_defaults_to_none(self):
        result = read_only_annotation()
        assert result.title is None

    def test_is_read_only(self):
        result = read_only_annotation()
        assert result.readOnlyHint is True

    def test_is_not_destructive(self):
        result = read_only_annotation()
        assert result.destructiveHint is False

    def test_is_idempotent(self):
        result = read_only_annotation()
        assert result.idempotentHint is True

    def test_is_not_open_world(self):
        result = read_only_annotation()
        assert result.openWorldHint is False


class TestCreateAnnotation:
    """Tests for create_annotation factory."""

    def test_returns_tool_annotations(self):
        result = create_annotation()
        assert isinstance(result, ToolAnnotations)

    def test_title_is_set(self):
        result = create_annotation("Create Story")
        assert result.title == "Create Story"

    def test_is_not_read_only(self):
        result = create_annotation()
        assert result.readOnlyHint is False

    def test_is_not_destructive(self):
        """Create operations are additive, not destructive."""
        result = create_annotation()
        assert result.destructiveHint is False

    def test_is_not_idempotent(self):
        """Create operations are not idempotent - each call creates new entity."""
        result = create_annotation()
        assert result.idempotentHint is False

    def test_is_not_open_world(self):
        result = create_annotation()
        assert result.openWorldHint is False


class TestUpdateAnnotation:
    """Tests for update_annotation factory."""

    def test_returns_tool_annotations(self):
        result = update_annotation()
        assert isinstance(result, ToolAnnotations)

    def test_title_is_set(self):
        result = update_annotation("Update Story")
        assert result.title == "Update Story"

    def test_is_not_read_only(self):
        result = update_annotation()
        assert result.readOnlyHint is False

    def test_is_destructive(self):
        """Update operations overwrite existing data."""
        result = update_annotation()
        assert result.destructiveHint is True

    def test_is_idempotent(self):
        """Same update applied twice yields same result."""
        result = update_annotation()
        assert result.idempotentHint is True

    def test_is_not_open_world(self):
        result = update_annotation()
        assert result.openWorldHint is False


class TestDeleteAnnotation:
    """Tests for delete_annotation factory."""

    def test_returns_tool_annotations(self):
        result = delete_annotation()
        assert isinstance(result, ToolAnnotations)

    def test_title_is_set(self):
        result = delete_annotation("Delete Story")
        assert result.title == "Delete Story"

    def test_is_not_read_only(self):
        result = delete_annotation()
        assert result.readOnlyHint is False

    def test_is_destructive(self):
        """Delete operations permanently remove data."""
        result = delete_annotation()
        assert result.destructiveHint is True

    def test_is_idempotent(self):
        """Deleting twice is a no-op (already gone)."""
        result = delete_annotation()
        assert result.idempotentHint is True

    def test_is_not_open_world(self):
        result = delete_annotation()
        assert result.openWorldHint is False


class TestDiagramAnnotation:
    """Tests for diagram_annotation factory."""

    def test_returns_tool_annotations(self):
        result = diagram_annotation()
        assert isinstance(result, ToolAnnotations)

    def test_title_is_set(self):
        result = diagram_annotation("System Context Diagram")
        assert result.title == "System Context Diagram"

    def test_is_read_only(self):
        """Diagrams are generated from existing data."""
        result = diagram_annotation()
        assert result.readOnlyHint is True

    def test_is_not_destructive(self):
        result = diagram_annotation()
        assert result.destructiveHint is False

    def test_is_idempotent(self):
        """Same input generates same diagram."""
        result = diagram_annotation()
        assert result.idempotentHint is True

    def test_is_not_open_world(self):
        result = diagram_annotation()
        assert result.openWorldHint is False


class TestAnnotationConsistency:
    """Tests for consistent behavior across annotation types."""

    @pytest.mark.parametrize(
        "factory,expected_read_only",
        [
            (read_only_annotation, True),
            (create_annotation, False),
            (update_annotation, False),
            (delete_annotation, False),
            (diagram_annotation, True),
        ],
    )
    def test_read_only_hint_matches_operation_type(self, factory, expected_read_only):
        result = factory()
        assert result.readOnlyHint is expected_read_only

    @pytest.mark.parametrize(
        "factory,expected_destructive",
        [
            (read_only_annotation, False),
            (create_annotation, False),
            (update_annotation, True),
            (delete_annotation, True),
            (diagram_annotation, False),
        ],
    )
    def test_destructive_hint_matches_operation_type(
        self, factory, expected_destructive
    ):
        result = factory()
        assert result.destructiveHint is expected_destructive

    @pytest.mark.parametrize(
        "factory,expected_idempotent",
        [
            (read_only_annotation, True),
            (create_annotation, False),
            (update_annotation, True),
            (delete_annotation, True),
            (diagram_annotation, True),
        ],
    )
    def test_idempotent_hint_matches_operation_type(self, factory, expected_idempotent):
        result = factory()
        assert result.idempotentHint is expected_idempotent

    @pytest.mark.parametrize(
        "factory",
        [
            read_only_annotation,
            create_annotation,
            update_annotation,
            delete_annotation,
            diagram_annotation,
        ],
    )
    def test_all_factories_have_open_world_false(self, factory):
        """All our tools operate on closed domain models, not open world."""
        result = factory()
        assert result.openWorldHint is False
