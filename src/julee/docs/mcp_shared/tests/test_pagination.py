"""Tests for pagination utilities."""

import pytest

from ..pagination import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    paginate_results,
)


class TestPaginationConstants:
    """Test pagination constant values."""

    def test_default_limit(self):
        """Default limit should be reasonable for typical use."""
        assert DEFAULT_LIMIT == 100
        assert DEFAULT_LIMIT > 0
        assert DEFAULT_LIMIT <= MAX_LIMIT

    def test_max_limit(self):
        """Max limit should prevent excessive responses."""
        assert MAX_LIMIT == 1000
        assert MAX_LIMIT > DEFAULT_LIMIT


class TestPaginateResults:
    """Test paginate_results function."""

    def test_empty_list(self):
        """Empty list should return empty result with correct structure."""
        result = paginate_results([])
        assert result["entities"] == []
        assert result["count"] == 0
        assert result["pagination"]["total"] == 0
        assert result["pagination"]["has_more"] is False

    def test_no_pagination_params(self):
        """Without params, should use defaults."""
        items = list(range(10))
        result = paginate_results(items)
        assert result["entities"] == items
        assert result["count"] == 10
        assert result["pagination"]["total"] == 10
        assert result["pagination"]["limit"] == DEFAULT_LIMIT
        assert result["pagination"]["offset"] == 0
        assert result["pagination"]["has_more"] is False

    def test_limit_applied(self):
        """Limit should restrict results."""
        items = list(range(20))
        result = paginate_results(items, limit=5)
        assert result["entities"] == [0, 1, 2, 3, 4]
        assert result["count"] == 5
        assert result["pagination"]["total"] == 20
        assert result["pagination"]["limit"] == 5
        assert result["pagination"]["has_more"] is True

    def test_offset_applied(self):
        """Offset should skip items."""
        items = list(range(10))
        result = paginate_results(items, offset=5)
        assert result["entities"] == [5, 6, 7, 8, 9]
        assert result["count"] == 5
        assert result["pagination"]["offset"] == 5
        assert result["pagination"]["has_more"] is False

    def test_limit_and_offset(self):
        """Both limit and offset should work together."""
        items = list(range(20))
        result = paginate_results(items, limit=5, offset=10)
        assert result["entities"] == [10, 11, 12, 13, 14]
        assert result["count"] == 5
        assert result["pagination"]["total"] == 20
        assert result["pagination"]["limit"] == 5
        assert result["pagination"]["offset"] == 10
        assert result["pagination"]["has_more"] is True

    def test_offset_beyond_end(self):
        """Offset past end should return empty results."""
        items = list(range(10))
        result = paginate_results(items, offset=100)
        assert result["entities"] == []
        assert result["count"] == 0
        assert result["pagination"]["total"] == 10
        assert result["pagination"]["offset"] == 10  # clamped to total
        assert result["pagination"]["has_more"] is False

    def test_negative_offset_clamped(self):
        """Negative offset should be clamped to 0."""
        items = list(range(10))
        result = paginate_results(items, offset=-5)
        assert result["pagination"]["offset"] == 0
        assert result["entities"] == items

    def test_limit_capped_at_max(self):
        """Limit should not exceed MAX_LIMIT."""
        items = list(range(10))
        result = paginate_results(items, limit=5000)
        assert result["pagination"]["limit"] == MAX_LIMIT

    def test_none_limit_uses_default(self):
        """None limit should use DEFAULT_LIMIT."""
        items = list(range(10))
        result = paginate_results(items, limit=None)
        assert result["pagination"]["limit"] == DEFAULT_LIMIT

    def test_zero_limit_uses_default(self):
        """Zero limit should use DEFAULT_LIMIT (or 0, depending on implementation)."""
        items = list(range(10))
        result = paginate_results(items, limit=0)
        # min(0 or DEFAULT_LIMIT, MAX_LIMIT) = min(DEFAULT_LIMIT, MAX_LIMIT) = DEFAULT_LIMIT
        assert result["pagination"]["limit"] == DEFAULT_LIMIT

    def test_has_more_false_at_end(self):
        """has_more should be False when at last page."""
        items = list(range(25))
        result = paginate_results(items, limit=10, offset=20)
        assert result["entities"] == [20, 21, 22, 23, 24]
        assert result["count"] == 5
        assert result["pagination"]["has_more"] is False

    def test_has_more_true_with_remaining(self):
        """has_more should be True when more items exist."""
        items = list(range(25))
        result = paginate_results(items, limit=10, offset=10)
        assert result["count"] == 10
        assert result["pagination"]["has_more"] is True

    def test_efficiency_hint_for_large_datasets(self):
        """Large datasets with more pages should include efficiency hint."""
        items = list(range(100))
        result = paginate_results(items, limit=10)
        assert "efficiency_hint" in result
        assert "offset=10" in result["efficiency_hint"]

    def test_no_efficiency_hint_for_small_datasets(self):
        """Small datasets should not include efficiency hint."""
        items = list(range(30))
        result = paginate_results(items, limit=10)
        # Total is 30, which is not > 50, so no hint
        assert "efficiency_hint" not in result

    def test_no_efficiency_hint_when_no_more_pages(self):
        """No hint when all items returned."""
        items = list(range(100))
        result = paginate_results(items, limit=200)
        # has_more is False, so no hint
        assert "efficiency_hint" not in result

    def test_dict_items(self):
        """Should work with dict items."""
        items = [{"id": i, "name": f"Item {i}"} for i in range(10)]
        result = paginate_results(items, limit=3)
        assert len(result["entities"]) == 3
        assert result["entities"][0] == {"id": 0, "name": "Item 0"}

    def test_preserves_item_order(self):
        """Items should maintain their order."""
        items = ["z", "a", "m", "b"]
        result = paginate_results(items)
        assert result["entities"] == ["z", "a", "m", "b"]

    def test_pagination_metadata_structure(self):
        """Pagination metadata should have correct structure."""
        items = list(range(100))
        result = paginate_results(items, limit=10, offset=20)
        pagination = result["pagination"]
        assert set(pagination.keys()) == {"total", "limit", "offset", "has_more"}
        assert isinstance(pagination["total"], int)
        assert isinstance(pagination["limit"], int)
        assert isinstance(pagination["offset"], int)
        assert isinstance(pagination["has_more"], bool)


class TestPaginationEdgeCases:
    """Test edge cases for pagination."""

    def test_single_item(self):
        """Single item should paginate correctly."""
        result = paginate_results(["only"])
        assert result["entities"] == ["only"]
        assert result["count"] == 1
        assert result["pagination"]["total"] == 1

    def test_exact_limit_boundary(self):
        """Exactly limit items should show no more."""
        items = list(range(10))
        result = paginate_results(items, limit=10)
        assert result["count"] == 10
        assert result["pagination"]["has_more"] is False

    def test_one_over_limit(self):
        """One more than limit should show has_more."""
        items = list(range(11))
        result = paginate_results(items, limit=10)
        assert result["count"] == 10
        assert result["pagination"]["has_more"] is True

    def test_last_page_partial(self):
        """Last page may have fewer items than limit."""
        items = list(range(25))
        result = paginate_results(items, limit=10, offset=20)
        assert result["count"] == 5
        assert len(result["entities"]) == 5
