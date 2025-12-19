"""Tests for response format utilities."""

import pytest

from ..response_format import (
    EXCLUDE_FIELDS,
    SUMMARY_FIELDS,
    ResponseFormat,
    format_entities,
    format_entity,
    get_format_param_description,
)


class TestResponseFormatEnum:
    """Test ResponseFormat enum."""

    def test_enum_values(self):
        """Enum should have correct string values."""
        assert ResponseFormat.SUMMARY.value == "summary"
        assert ResponseFormat.FULL.value == "full"
        assert ResponseFormat.EXTENDED.value == "extended"

    def test_from_string_valid(self):
        """from_string should parse valid values."""
        assert ResponseFormat.from_string("summary") == ResponseFormat.SUMMARY
        assert ResponseFormat.from_string("full") == ResponseFormat.FULL
        assert ResponseFormat.from_string("extended") == ResponseFormat.EXTENDED

    def test_from_string_case_insensitive(self):
        """from_string should be case insensitive."""
        assert ResponseFormat.from_string("SUMMARY") == ResponseFormat.SUMMARY
        assert ResponseFormat.from_string("Full") == ResponseFormat.FULL
        assert ResponseFormat.from_string("EXTENDED") == ResponseFormat.EXTENDED

    def test_from_string_invalid_defaults_to_full(self):
        """Invalid format strings should default to FULL."""
        assert ResponseFormat.from_string("invalid") == ResponseFormat.FULL
        assert ResponseFormat.from_string("brief") == ResponseFormat.FULL
        assert ResponseFormat.from_string("") == ResponseFormat.FULL

    def test_from_string_none_defaults_to_full(self):
        """None should default to FULL."""
        assert ResponseFormat.from_string(None) == ResponseFormat.FULL


class TestSummaryFields:
    """Test summary field definitions."""

    def test_hcd_entities_defined(self):
        """HCD entity types should have summary fields."""
        hcd_types = ["story", "epic", "journey", "persona", "app", "accelerator", "integration"]
        for entity_type in hcd_types:
            assert entity_type in SUMMARY_FIELDS
            assert len(SUMMARY_FIELDS[entity_type]) > 0
            assert "slug" in SUMMARY_FIELDS[entity_type] or "name" in SUMMARY_FIELDS[entity_type]

    def test_c4_entities_defined(self):
        """C4 entity types should have summary fields."""
        c4_types = [
            "software_system",
            "container",
            "component",
            "relationship",
            "deployment_node",
            "dynamic_step",
        ]
        for entity_type in c4_types:
            assert entity_type in SUMMARY_FIELDS
            assert len(SUMMARY_FIELDS[entity_type]) > 0

    def test_slug_in_most_summaries(self):
        """Most entity types should include slug in summary."""
        for entity_type, fields in SUMMARY_FIELDS.items():
            # All types should have slug
            assert "slug" in fields, f"{entity_type} should have slug in summary"


class TestExcludeFields:
    """Test excluded field definitions."""

    def test_internal_fields_excluded(self):
        """Internal/computed fields should be excluded."""
        expected_excludes = ["abs_path", "manifest_path"]
        for field in expected_excludes:
            assert field in EXCLUDE_FIELDS

    def test_normalized_fields_excluded(self):
        """Normalized fields should be excluded."""
        normalized = [f for f in EXCLUDE_FIELDS if "normalized" in f.lower()]
        assert len(normalized) > 0


class TestFormatEntity:
    """Test format_entity function."""

    @pytest.fixture
    def sample_story(self):
        """Sample story entity."""
        return {
            "slug": "login-flow",
            "feature_title": "User Login",
            "persona": "Staff Member",
            "app_slug": "hr-portal",
            "i_want": "log in securely",
            "so_that": "I can access my data",
            "description": "Full login flow description",
            "abs_path": "/internal/path",
        }

    @pytest.fixture
    def sample_system(self):
        """Sample software system entity."""
        return {
            "slug": "banking-system",
            "name": "Internet Banking",
            "system_type": "internal",
            "description": "Main banking application",
            "owner": "Platform Team",
            "technology": "Python, PostgreSQL",
            "abs_path": "/internal/path",
        }

    def test_summary_format_filters_fields(self, sample_story):
        """Summary format should only include defined fields."""
        result = format_entity(sample_story, ResponseFormat.SUMMARY, "story")
        assert "slug" in result
        assert "feature_title" in result
        assert "persona" in result
        assert "app_slug" in result
        assert "i_want" not in result
        assert "so_that" not in result
        assert "abs_path" not in result

    def test_full_format_excludes_internal(self, sample_story):
        """Full format should exclude internal fields."""
        result = format_entity(sample_story, ResponseFormat.FULL, "story")
        assert "slug" in result
        assert "feature_title" in result
        assert "i_want" in result
        assert "so_that" in result
        assert "abs_path" not in result

    def test_extended_format_includes_relationships(self, sample_story):
        """Extended format should include relationships."""
        relationships = {"epics": ["auth-epic"], "journeys": ["login-journey"]}
        result = format_entity(
            sample_story, ResponseFormat.EXTENDED, "story", relationships=relationships
        )
        assert "_relationships" in result
        assert result["_relationships"] == relationships

    def test_extended_without_relationships(self, sample_story):
        """Extended format without relationships should work."""
        result = format_entity(sample_story, ResponseFormat.EXTENDED, "story")
        assert "_relationships" not in result

    def test_string_format_accepted(self, sample_story):
        """String format should be converted to enum."""
        result = format_entity(sample_story, "summary", "story")
        assert "slug" in result
        assert "i_want" not in result

    def test_unknown_entity_type_defaults(self):
        """Unknown entity type should use default fields."""
        entity = {"slug": "test", "name": "Test", "other": "value"}
        result = format_entity(entity, ResponseFormat.SUMMARY, "unknown_type")
        # Should default to ["slug", "name"]
        assert "slug" in result
        assert "name" in result
        assert "other" not in result

    def test_c4_entity_summary(self, sample_system):
        """C4 entities should format correctly."""
        result = format_entity(sample_system, ResponseFormat.SUMMARY, "software_system")
        assert "slug" in result
        assert "name" in result
        assert "system_type" in result
        assert "description" not in result
        assert "owner" not in result

    def test_preserves_original(self, sample_story):
        """Original entity should not be modified."""
        original_keys = set(sample_story.keys())
        format_entity(sample_story, ResponseFormat.SUMMARY, "story")
        assert set(sample_story.keys()) == original_keys


class TestFormatEntities:
    """Test format_entities function."""

    def test_formats_list_of_entities(self):
        """Should format a list of entities."""
        entities = [
            {"slug": "a", "name": "A", "extra": "x"},
            {"slug": "b", "name": "B", "extra": "y"},
        ]
        result = format_entities(entities, ResponseFormat.SUMMARY, "software_system")
        assert len(result) == 2
        assert all("slug" in e for e in result)
        assert all("name" in e for e in result)
        # system_type not in these entities but that's ok

    def test_empty_list(self):
        """Empty list should return empty list."""
        result = format_entities([], ResponseFormat.SUMMARY, "story")
        assert result == []

    def test_single_entity(self):
        """Single entity list should work."""
        result = format_entities([{"slug": "only"}], ResponseFormat.SUMMARY, "epic")
        assert len(result) == 1


class TestGetFormatParamDescription:
    """Test documentation helper."""

    def test_returns_string(self):
        """Should return a non-empty string."""
        desc = get_format_param_description()
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_includes_format_options(self):
        """Description should mention all format options."""
        desc = get_format_param_description()
        assert "summary" in desc.lower()
        assert "full" in desc.lower()
        assert "extended" in desc.lower()


class TestFormatEntityEdgeCases:
    """Test edge cases for entity formatting."""

    def test_missing_summary_field_handled(self):
        """Missing fields should not cause errors."""
        entity = {"slug": "test"}  # Missing other summary fields
        result = format_entity(entity, ResponseFormat.SUMMARY, "story")
        assert "slug" in result
        # Missing fields just aren't in result
        assert "feature_title" not in result

    def test_empty_entity(self):
        """Empty entity should return empty dict for summary."""
        result = format_entity({}, ResponseFormat.SUMMARY, "story")
        assert result == {}

    def test_none_values_preserved(self):
        """None values should be preserved."""
        entity = {"slug": "test", "name": None}
        result = format_entity(entity, ResponseFormat.FULL, "app")
        assert result.get("name") is None

    def test_nested_data_preserved(self):
        """Nested structures should be preserved."""
        entity = {
            "slug": "test",
            "metadata": {"created": "2024-01-01", "tags": ["a", "b"]},
        }
        result = format_entity(entity, ResponseFormat.FULL, "app")
        assert result["metadata"] == {"created": "2024-01-01", "tags": ["a", "b"]}
