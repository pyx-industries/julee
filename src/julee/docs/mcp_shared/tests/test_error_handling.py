"""Tests for error handling utilities."""

import pytest

from ..error_handling import (
    ErrorType,
    conflict_error,
    find_similar,
    not_found_error,
    permission_error,
    reference_error,
    validation_error,
)


class TestErrorTypeConstants:
    """Test error type constants."""

    def test_error_types_exist(self):
        """All error types should be defined."""
        assert ErrorType.NOT_FOUND == "NOT_FOUND"
        assert ErrorType.VALIDATION == "VALIDATION"
        assert ErrorType.CONFLICT == "CONFLICT"
        assert ErrorType.REFERENCE == "REFERENCE"
        assert ErrorType.PERMISSION == "PERMISSION"


class TestFindSimilar:
    """Test find_similar function."""

    def test_exact_match(self):
        """Exact match should be returned."""
        result = find_similar("test", ["test", "other"])
        assert "test" in result

    def test_close_match(self):
        """Close matches should be found."""
        result = find_similar("tset", ["test", "other", "unrelated"])
        assert "test" in result

    def test_case_insensitive(self):
        """Matching should be case insensitive."""
        result = find_similar("TEST", ["test", "other"])
        assert "test" in result

    def test_max_results_limit(self):
        """Should respect max_results."""
        candidates = ["test1", "test2", "test3", "test4", "test5"]
        result = find_similar("test", candidates, max_results=2)
        assert len(result) <= 2

    def test_threshold_filtering(self):
        """Should filter by threshold."""
        result = find_similar("test", ["aaaa", "bbbb"], threshold=0.8)
        assert len(result) == 0

    def test_empty_target(self):
        """Empty target should return empty list."""
        result = find_similar("", ["test", "other"])
        assert result == []

    def test_empty_candidates(self):
        """Empty candidates should return empty list."""
        result = find_similar("test", [])
        assert result == []

    def test_sorted_by_similarity(self):
        """Results should be sorted by similarity."""
        result = find_similar("test", ["test", "tost", "unrelated"])
        # Exact match should come first
        if len(result) > 0:
            assert result[0] == "test"


class TestNotFoundError:
    """Test not_found_error function."""

    def test_basic_not_found(self):
        """Basic not found error structure."""
        result = not_found_error("story", "my-story")
        assert result["entity"] is None
        assert result["found"] is False
        assert result["error"]["type"] == ErrorType.NOT_FOUND
        assert "story" in result["error"]["message"].lower()
        assert "my-story" in result["error"]["message"]

    def test_with_similar_suggestions(self):
        """Should include similar slugs when available."""
        result = not_found_error("story", "my-story", ["my-stories", "your-story"])
        assert result["error"].get("similar")
        assert len(result["suggestions"]) > 0
        # Check suggestion references typo (category is "typo_suggestion")
        assert any("typo" in s.get("category", "") for s in result["suggestions"])

    def test_without_similar(self):
        """Should suggest listing when no similar found."""
        result = not_found_error("container", "xyz", ["aaa", "bbb"])
        # No similar matches for "xyz"
        suggestions = result["suggestions"]
        assert len(suggestions) > 0
        # Should suggest listing
        assert any("list_" in (s.get("tool") or "") for s in suggestions)

    def test_entity_type_formatting(self):
        """Entity type should be formatted nicely."""
        result = not_found_error("software_system", "test")
        # Should convert underscores to spaces
        assert "Software System" in result["error"]["message"]


class TestValidationError:
    """Test validation_error function."""

    def test_basic_validation(self):
        """Basic validation error structure."""
        result = validation_error("Invalid input")
        assert result["success"] is False
        assert result["entity"] is None
        assert result["error"]["type"] == ErrorType.VALIDATION
        assert result["error"]["message"] == "Invalid input"

    def test_with_field(self):
        """Validation error with field specified."""
        result = validation_error("Name too long", field="name")
        assert result["error"]["field"] == "name"

    def test_with_details(self):
        """Validation error with extra details."""
        result = validation_error(
            "Invalid format",
            details={"expected": "slug", "got": "with spaces"},
        )
        # Details should be in suggestions context
        assert result["suggestions"][0]["context"]["expected"] == "slug"


class TestConflictError:
    """Test conflict_error function."""

    def test_basic_conflict(self):
        """Basic conflict error structure."""
        result = conflict_error("story", "existing-story")
        assert result["success"] is False
        assert result["error"]["type"] == ErrorType.CONFLICT
        assert "existing-story" in result["error"]["message"]

    def test_custom_conflict_type(self):
        """Conflict with custom description."""
        result = conflict_error("app", "my-app", "conflicts with reserved name")
        assert "conflicts with reserved name" in result["error"]["message"]

    def test_update_suggestion(self):
        """Should suggest using update instead."""
        result = conflict_error("container", "web-app")
        suggestions = result["suggestions"]
        assert any("update_container" in (s.get("tool") or "") for s in suggestions)


class TestReferenceError:
    """Test reference_error function."""

    def test_basic_reference(self):
        """Basic reference error structure."""
        result = reference_error(
            entity_type="container",
            identifier="my-container",
            referenced_type="software_system",
            referenced_id="missing-system",
        )
        assert result["success"] is False
        assert result["error"]["type"] == ErrorType.REFERENCE
        assert "missing-system" in result["error"]["message"]
        assert result["error"]["field"] == "software_system_slug"

    def test_with_similar_references(self):
        """Should suggest similar references when available."""
        result = reference_error(
            entity_type="component",
            identifier="my-comp",
            referenced_type="container",
            referenced_id="web-ap",
            available=["web-app", "api-app"],
        )
        assert "web-app" in result["error"].get("similar", [])

    def test_create_suggestion(self):
        """Should suggest creating the missing reference."""
        result = reference_error(
            entity_type="container",
            identifier="my-container",
            referenced_type="software_system",
            referenced_id="new-system",
        )
        suggestions = result["suggestions"]
        assert any("create_software_system" in (s.get("tool") or "") for s in suggestions)


class TestPermissionError:
    """Test permission_error function."""

    def test_basic_permission(self):
        """Basic permission error structure."""
        result = permission_error("delete", "software_system")
        assert result["success"] is False
        assert result["error"]["type"] == ErrorType.PERMISSION
        assert "delete" in result["error"]["message"]
        assert "software system" in result["error"]["message"].lower()

    def test_custom_reason(self):
        """Permission error with custom reason."""
        result = permission_error("update", "app", reason="read-only in production")
        assert "read-only in production" in result["error"]["message"]

    def test_suggestion_context(self):
        """Permission error should include operation context."""
        result = permission_error("delete", "story")
        context = result["suggestions"][0]["context"]
        assert context["operation"] == "delete"
        assert context["entity_type"] == "story"


class TestErrorResponseStructure:
    """Test that all error functions return consistent structures."""

    def test_not_found_has_required_keys(self):
        """not_found_error should have required keys."""
        result = not_found_error("test", "id")
        assert "entity" in result
        assert "found" in result
        assert "error" in result
        assert "suggestions" in result

    def test_validation_has_required_keys(self):
        """validation_error should have required keys."""
        result = validation_error("msg")
        assert "success" in result
        assert "entity" in result
        assert "error" in result
        assert "suggestions" in result

    def test_conflict_has_required_keys(self):
        """conflict_error should have required keys."""
        result = conflict_error("type", "id")
        assert "success" in result
        assert "entity" in result
        assert "error" in result
        assert "suggestions" in result

    def test_reference_has_required_keys(self):
        """reference_error should have required keys."""
        result = reference_error("type", "id", "ref_type", "ref_id")
        assert "success" in result
        assert "entity" in result
        assert "error" in result
        assert "suggestions" in result

    def test_permission_has_required_keys(self):
        """permission_error should have required keys."""
        result = permission_error("op", "type")
        assert "success" in result
        assert "entity" in result
        assert "error" in result
        assert "suggestions" in result
