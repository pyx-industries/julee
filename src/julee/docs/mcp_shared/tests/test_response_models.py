"""Tests for response model utilities."""

import pytest
from pydantic import ValidationError

from ..response_models import (
    ErrorInfo,
    MCPGetResponse,
    MCPListResponse,
    MCPMutationResponse,
    PaginationInfo,
    SuggestionInfo,
    get_response,
    list_response,
    mutation_response,
)


class TestPaginationInfo:
    """Test PaginationInfo model."""

    def test_valid_pagination(self):
        """Valid pagination info should be created."""
        info = PaginationInfo(total=100, limit=10, offset=0, has_more=True)
        assert info.total == 100
        assert info.limit == 10
        assert info.offset == 0
        assert info.has_more is True

    def test_model_dump(self):
        """Model should serialize correctly."""
        info = PaginationInfo(total=50, limit=25, offset=25, has_more=False)
        data = info.model_dump()
        assert data == {"total": 50, "limit": 25, "offset": 25, "has_more": False}


class TestSuggestionInfo:
    """Test SuggestionInfo model."""

    def test_minimal_suggestion(self):
        """Suggestion with required fields only."""
        info = SuggestionInfo(
            severity="info",
            category="next_step",
            message="Do something",
            action="Take action",
        )
        assert info.severity == "info"
        assert info.tool is None
        assert info.context == {}

    def test_full_suggestion(self):
        """Suggestion with all fields."""
        info = SuggestionInfo(
            severity="warning",
            category="incomplete",
            message="Missing data",
            action="Add the data",
            tool="update_story",
            context={"slug": "test"},
        )
        assert info.tool == "update_story"
        assert info.context == {"slug": "test"}


class TestErrorInfo:
    """Test ErrorInfo model."""

    def test_minimal_error(self):
        """Error with required fields only."""
        info = ErrorInfo(type="NOT_FOUND", message="Not found")
        assert info.type == "NOT_FOUND"
        assert info.field is None
        assert info.similar == []

    def test_full_error(self):
        """Error with all fields."""
        info = ErrorInfo(
            type="VALIDATION",
            message="Invalid input",
            field="name",
            similar=["name1", "name2"],
        )
        assert info.field == "name"
        assert info.similar == ["name1", "name2"]


class TestMCPGetResponse:
    """Test MCPGetResponse model."""

    def test_found_response(self):
        """Response when entity is found."""
        response = MCPGetResponse(
            entity={"slug": "test", "name": "Test"},
            found=True,
        )
        assert response.found is True
        assert response.entity["slug"] == "test"
        assert response.suggestions == []
        assert response.error is None

    def test_not_found_response(self):
        """Response when entity is not found."""
        response = MCPGetResponse(
            entity=None,
            found=False,
            error=ErrorInfo(type="NOT_FOUND", message="Not found"),
        )
        assert response.found is False
        assert response.entity is None
        assert response.error is not None
        assert response.error.type == "NOT_FOUND"

    def test_with_suggestions(self):
        """Response with suggestions."""
        response = MCPGetResponse(
            entity={"slug": "test"},
            found=True,
            suggestions=[
                SuggestionInfo(
                    severity="info",
                    category="next_step",
                    message="Test",
                    action="Do it",
                )
            ],
        )
        assert len(response.suggestions) == 1


class TestMCPListResponse:
    """Test MCPListResponse model."""

    def test_list_response(self):
        """Basic list response."""
        response = MCPListResponse(
            entities=[{"slug": "a"}, {"slug": "b"}],
            count=2,
            pagination=PaginationInfo(total=2, limit=100, offset=0, has_more=False),
        )
        assert response.count == 2
        assert len(response.entities) == 2
        assert response.efficiency_hint is None

    def test_with_efficiency_hint(self):
        """List response with efficiency hint."""
        response = MCPListResponse(
            entities=[{"slug": "a"}],
            count=1,
            pagination=PaginationInfo(total=100, limit=1, offset=0, has_more=True),
            efficiency_hint="Use offset=1 for next page",
        )
        assert response.efficiency_hint is not None


class TestMCPMutationResponse:
    """Test MCPMutationResponse model."""

    def test_success_response(self):
        """Successful mutation response."""
        response = MCPMutationResponse(
            success=True,
            entity={"slug": "new"},
        )
        assert response.success is True
        assert response.entity["slug"] == "new"
        assert response.error is None

    def test_failure_response(self):
        """Failed mutation response."""
        response = MCPMutationResponse(
            success=False,
            entity=None,
            error=ErrorInfo(type="CONFLICT", message="Already exists"),
        )
        assert response.success is False
        assert response.error.type == "CONFLICT"


class TestGetResponseHelper:
    """Test get_response helper function."""

    def test_found_entity(self):
        """Build response for found entity."""
        result = get_response(
            entity={"slug": "test"},
            found=True,
        )
        assert result["found"] is True
        assert result["entity"]["slug"] == "test"
        assert "error" not in result  # exclude_none

    def test_not_found_entity(self):
        """Build response for not found entity."""
        result = get_response(
            entity=None,
            found=False,
            error={"type": "NOT_FOUND", "message": "Not found"},
        )
        assert result["found"] is False
        assert result["error"]["type"] == "NOT_FOUND"

    def test_with_suggestions(self):
        """Build response with suggestions."""
        result = get_response(
            entity={"slug": "test"},
            found=True,
            suggestions=[
                {
                    "severity": "info",
                    "category": "next",
                    "message": "msg",
                    "action": "act",
                }
            ],
        )
        assert len(result["suggestions"]) == 1


class TestListResponseHelper:
    """Test list_response helper function."""

    def test_basic_list(self):
        """Build basic list response."""
        result = list_response(
            entities=[{"slug": "a"}, {"slug": "b"}],
            pagination={"total": 2, "limit": 100, "offset": 0, "has_more": False},
        )
        assert result["count"] == 2
        assert len(result["entities"]) == 2
        assert result["pagination"]["total"] == 2

    def test_with_hint(self):
        """Build list response with hint."""
        result = list_response(
            entities=[{"slug": "a"}],
            pagination={"total": 100, "limit": 1, "offset": 0, "has_more": True},
            efficiency_hint="Use offset=1",
        )
        assert result["efficiency_hint"] == "Use offset=1"


class TestMutationResponseHelper:
    """Test mutation_response helper function."""

    def test_success_mutation(self):
        """Build success mutation response."""
        result = mutation_response(
            success=True,
            entity={"slug": "created"},
        )
        assert result["success"] is True
        assert result["entity"]["slug"] == "created"

    def test_failure_mutation(self):
        """Build failure mutation response."""
        result = mutation_response(
            success=False,
            error={"type": "VALIDATION", "message": "Invalid"},
        )
        assert result["success"] is False
        assert result["error"]["type"] == "VALIDATION"

    def test_delete_mutation(self):
        """Build delete mutation response (no entity)."""
        result = mutation_response(
            success=True,
            entity=None,
            suggestions=[
                {
                    "severity": "info",
                    "category": "next",
                    "message": "Deleted",
                    "action": "Continue",
                }
            ],
        )
        assert result["success"] is True
        assert "entity" not in result  # exclude_none
