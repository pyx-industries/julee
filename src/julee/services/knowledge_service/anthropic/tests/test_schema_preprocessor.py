"""
Tests for AnthropicSchemaPreprocessor.

This module tests the schema preprocessing functionality that makes JSON schemas
compatible with Anthropic's structured outputs limitations.
"""

from unittest.mock import patch

import pytest

from julee.services.knowledge_service.anthropic.schema_preprocessor import (
    AnthropicSchemaPreprocessor,
)


class TestAnthropicSchemaPreprocessor:
    """Test cases for AnthropicSchemaPreprocessor."""

    @pytest.fixture
    def preprocessor(self) -> AnthropicSchemaPreprocessor:
        """Create a preprocessor instance for testing."""
        return AnthropicSchemaPreprocessor()

    def test_leaves_compatible_schemas_unchanged(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test that compatible schemas are left unchanged."""
        # Schema with minItems 0 (default)
        schema1 = {
            "type": "object",
            "properties": {"tags": {"type": "array", "items": {"type": "string"}}},
        }

        compatible1, changes1 = preprocessor.make_compatible(schema1)
        assert compatible1 == schema1
        assert changes1 == []

        # Schema with minItems 1 (valid)
        schema2 = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string"},
                }
            },
        }

        compatible2, changes2 = preprocessor.make_compatible(schema2)
        assert compatible2 == schema2
        assert changes2 == []

        # Schema with minItems 0 (explicit)
        schema3 = {
            "type": "array",
            "minItems": 0,
            "items": {"type": "number"},
        }

        compatible3, changes3 = preprocessor.make_compatible(schema3)
        assert compatible3 == schema3
        assert changes3 == []

    def test_reduces_high_min_items_to_one(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test that minItems > 1 are reduced to 1."""
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 10,
                    "items": {"type": "string"},
                }
            },
        }

        compatible, changes = preprocessor.make_compatible(schema)

        # Should modify minItems but preserve other constraints
        expected = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "minItems": 1,  # Changed from 3
                    "maxItems": 10,  # Preserved
                    "items": {"type": "string"},  # Preserved
                }
            },
        }

        assert compatible == expected
        assert len(changes) == 1
        assert "properties.tags.minItems" in changes[0]
        assert "reduced from 3 to 1" in changes[0]

    def test_handles_multiple_min_items_violations(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test schema with multiple minItems violations."""
        schema = {
            "type": "object",
            "properties": {
                "tags": {"type": "array", "minItems": 2},
                "categories": {"type": "array", "minItems": 5},
                "normal": {"type": "array", "minItems": 1},  # Should be unchanged
            },
        }

        compatible, changes = preprocessor.make_compatible(schema)

        # Both violations should be fixed
        assert compatible["properties"]["tags"]["minItems"] == 1
        assert compatible["properties"]["categories"]["minItems"] == 1
        assert compatible["properties"]["normal"]["minItems"] == 1  # Unchanged

        assert len(changes) == 2
        assert any("properties.tags.minItems" in change for change in changes)
        assert any("properties.categories.minItems" in change for change in changes)

    def test_handles_nested_schemas(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test minItems fixes in deeply nested schema structures."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {
                                "skills": {
                                    "type": "array",
                                    "minItems": 4,
                                    "items": {"type": "string"},
                                }
                            },
                        }
                    },
                }
            },
        }

        compatible, changes = preprocessor.make_compatible(schema)

        assert (
            compatible["properties"]["user"]["properties"]["profile"]["properties"][
                "skills"
            ]["minItems"]
            == 1
        )

        assert len(changes) == 1
        assert (
            "properties.user.properties.profile.properties.skills.minItems"
            in changes[0]
        )

    def test_handles_definitions_and_defs(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test minItems fixes in definitions and $defs sections."""
        schema = {
            "type": "object",
            "definitions": {
                "TagList": {"type": "array", "minItems": 3, "items": {"type": "string"}}
            },
            "$defs": {
                "CategoryList": {
                    "type": "array",
                    "minItems": 2,
                    "items": {"type": "string"},
                }
            },
            "properties": {
                "tags": {"$ref": "#/definitions/TagList"},
                "categories": {"$ref": "#/$defs/CategoryList"},
            },
        }

        compatible, changes = preprocessor.make_compatible(schema)

        assert compatible["definitions"]["TagList"]["minItems"] == 1
        assert compatible["$defs"]["CategoryList"]["minItems"] == 1

        assert len(changes) == 2
        assert any("definitions.TagList.minItems" in change for change in changes)
        assert any("$defs.CategoryList.minItems" in change for change in changes)

    def test_handles_array_of_schemas(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test schemas within arrays (like allOf, anyOf)."""
        schema = {
            "allOf": [
                {"type": "array", "minItems": 2},
                {"type": "array", "minItems": 3},
            ]
        }

        compatible, changes = preprocessor.make_compatible(schema)

        assert compatible["allOf"][0]["minItems"] == 1
        assert compatible["allOf"][1]["minItems"] == 1

        assert len(changes) == 2
        assert any("allOf[0].minItems" in change for change in changes)
        assert any("allOf[1].minItems" in change for change in changes)

    def test_preserves_other_array_constraints(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test that other array constraints are preserved."""
        schema = {
            "type": "array",
            "minItems": 5,
            "maxItems": 10,
            "uniqueItems": True,
            "items": {"type": "string", "pattern": "^[A-Z]+$"},
            "description": "List of uppercase strings",
        }

        compatible, changes = preprocessor.make_compatible(schema)

        # minItems and uniqueItems should change
        expected = {
            "type": "array",
            "minItems": 1,  # reduced from 5
            "maxItems": 10,
            # uniqueItems removed (not supported by Anthropic)
            "items": {"type": "string", "pattern": "^[A-Z]+$"},
            "description": "List of uppercase strings",
        }

        assert compatible == expected
        assert len(changes) == 2
        assert any("minItems: reduced from 5 to 1" in change for change in changes)
        assert any(
            "uniqueItems: removed (not supported by Anthropic)" in change
            for change in changes
        )

    def test_handles_root_level_array(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test schema where root is an array with minItems."""
        schema = {
            "type": "array",
            "minItems": 4,
            "items": {"type": "string"},
        }

        compatible, changes = preprocessor.make_compatible(schema)

        assert compatible["minItems"] == 1
        assert len(changes) == 1
        assert "root.minItems" in changes[0]

    def test_quick_scan_optimization(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test that compatible schemas are quickly detected without deep copying."""
        large_compatible_schema = {
            "type": "object",
            "properties": {
                f"field_{i}": {
                    "type": "array",
                    "minItems": 1 if i % 2 == 0 else 0,
                    "items": {"type": "string"},
                }
                for i in range(100)
            },
        }

        with patch("copy.deepcopy") as mock_deepcopy:
            compatible, changes = preprocessor.make_compatible(large_compatible_schema)

            # Should not call deepcopy since no changes needed
            mock_deepcopy.assert_not_called()
            assert compatible == large_compatible_schema
            assert changes == []

    def test_error_handling_preserves_original_schema(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test that errors in processing return original schema safely."""
        schema = {"type": "array", "minItems": 3}

        # Mock an error in the processing
        with patch.object(
            preprocessor,
            "_process_schema_recursively",
            side_effect=ValueError("Test error"),
        ):
            compatible, changes = preprocessor.make_compatible(schema)

            # Should return original schema unchanged
            assert compatible == schema
            assert changes == []

    def test_non_integer_min_items_ignored(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test that non-integer minItems values are ignored."""
        schema = {
            "type": "array",
            "minItems": "3",  # String instead of int
            "items": {"type": "string"},
        }

        compatible, changes = preprocessor.make_compatible(schema)

        # Should be unchanged since minItems is not an integer
        assert compatible == schema
        assert changes == []

    def test_complex_real_world_schema(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test with a complex schema similar to real assembly specifications."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "type": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 5,
                    "items": {"type": "string"},
                },
                "credentialSubject": {
                    "type": "object",
                    "properties": {
                        "conformityClaim": {
                            "type": "array",
                            "minItems": 1,  # Should be unchanged
                            "items": {
                                "type": "object",
                                "properties": {
                                    "assessmentCriteria": {
                                        "type": "array",
                                        "minItems": 3,  # Should be changed
                                        "items": {"type": "string"},
                                    }
                                },
                            },
                        }
                    },
                },
            },
            "$defs": {
                "TagArray": {
                    "type": "array",
                    "minItems": 4,  # Should be changed
                    "items": {"type": "string"},
                }
            },
        }

        compatible, changes = preprocessor.make_compatible(schema)

        # Check the changes
        assert compatible["properties"]["type"]["minItems"] == 1
        assert (
            compatible["properties"]["credentialSubject"]["properties"][
                "conformityClaim"
            ]["minItems"]
            == 1
        )  # Unchanged
        assert (
            compatible["properties"]["credentialSubject"]["properties"][
                "conformityClaim"
            ]["items"]["properties"]["assessmentCriteria"]["minItems"]
            == 1
        )
        assert compatible["$defs"]["TagArray"]["minItems"] == 1

        # Should have 3 changes (not 4, since one was already 1)
        assert len(changes) == 3
        assert any("properties.type.minItems" in change for change in changes)
        assert any("assessmentCriteria.minItems" in change for change in changes)
        assert any("$defs.TagArray.minItems" in change for change in changes)

    def test_removes_unsupported_prefix_items(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test that prefixItems constraint is removed."""
        schema = {
            "type": "array",
            "prefixItems": [
                {"type": "string"},
                {"type": "number"},
                {"type": "boolean"},
            ],
            "maxItems": 3,
        }

        compatible, changes = preprocessor.make_compatible(schema)

        # prefixItems should be removed
        assert "prefixItems" not in compatible
        # Other constraints should be preserved
        assert compatible["maxItems"] == 3
        # Should add generic items schema based on first prefixItem
        assert compatible["items"] == {"type": "string"}

        assert len(changes) == 1
        assert "prefixItems: removed" in changes[0]
        assert "not supported by Anthropic" in changes[0]

    def test_prefix_items_with_existing_items_schema(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test prefixItems removal when items schema already exists."""
        schema = {
            "type": "array",
            "prefixItems": [
                {"type": "string"},
                {"type": "number"},
            ],
            "items": {"type": "object"},  # Existing items schema
        }

        compatible, changes = preprocessor.make_compatible(schema)

        # prefixItems should be removed
        assert "prefixItems" not in compatible
        # Existing items schema should be preserved
        assert compatible["items"] == {"type": "object"}

        assert len(changes) == 1
        assert "prefixItems: removed" in changes[0]

    def test_handles_both_min_items_and_prefix_items(
        self, preprocessor: AnthropicSchemaPreprocessor
    ) -> None:
        """Test schema with both minItems and prefixItems violations."""
        schema = {
            "type": "array",
            "minItems": 4,
            "prefixItems": [
                {"type": "string"},
                {"type": "number"},
            ],
        }

        compatible, changes = preprocessor.make_compatible(schema)

        # Both constraints should be fixed
        assert compatible["minItems"] == 1
        assert "prefixItems" not in compatible
        assert compatible["items"] == {"type": "string"}

        assert len(changes) == 2
        assert any("minItems" in change for change in changes)
        assert any("prefixItems" in change for change in changes)

    def test_logging_behavior(
        self, preprocessor: AnthropicSchemaPreprocessor, caplog
    ) -> None:
        """Test that appropriate log messages are generated."""
        schema = {
            "type": "array",
            "minItems": 3,
        }

        with caplog.at_level("INFO"):
            compatible, changes = preprocessor.make_compatible(schema)

        # Should log info about changes made
        assert "Schema modified for Anthropic compatibility" in caplog.text
        assert "1 changes made" in caplog.text

    def test_constraint_removal_table_based(self, preprocessor, subtests):
        """Test constraint removal using table-based approach for better maintainability."""
        # Format: (test_name, input_schema, expected_removals, expected_changes_count)
        test_cases = [
            # Array constraints
            (
                "uniqueItems_true",
                {"type": "array", "uniqueItems": True, "items": {"type": "string"}},
                ["uniqueItems"],
                1,
            ),
            (
                "uniqueItems_false",
                {"type": "array", "uniqueItems": False, "items": {"type": "number"}},
                ["uniqueItems"],
                1,
            ),
            (
                "contains_constraint",
                {
                    "type": "array",
                    "contains": {"type": "string"},
                    "items": {"type": "string"},
                },
                ["contains"],
                1,
            ),
            (
                "contains_non_array_preserved",
                {
                    "type": "object",
                    "properties": {"data": {"type": "string"}},
                    "contains": {"type": "string"},  # This should be preserved
                },
                [],  # No removals expected
                0,  # No changes expected
            ),
            (
                "contains_nested_allOf",
                {
                    "type": "array",
                    "items": {"type": "string"},
                    "allOf": [
                        {
                            "contains": {
                                "const": "DigitalProductPassport",
                                "minContains": 1,
                            }
                        },
                        {
                            "contains": {
                                "const": "VerifiableCredential",
                                "minContains": 1,
                            }
                        },
                    ],
                },
                [],  # No direct removals, but nested contains should be removed
                2,  # Two nested contains removals
            ),
            # Numerical constraints
            (
                "minimum_maximum",
                {"type": "number", "minimum": 0, "maximum": 100},
                ["minimum", "maximum"],
                2,
            ),
            (
                "multipleOf",
                {"type": "integer", "multipleOf": 5},
                ["multipleOf"],
                1,
            ),
            (
                "exclusive_constraints",
                {"type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 100},
                ["exclusiveMinimum", "exclusiveMaximum"],
                2,
            ),
            # String constraints
            (
                "string_length_constraints",
                {"type": "string", "minLength": 5, "maxLength": 50},
                ["minLength", "maxLength"],
                2,
            ),
            (
                "string_binary_format",
                {"type": "string", "format": "binary", "description": "Base64 data"},
                ["format"],
                1,
            ),
            (
                "string_supported_format_preserved",
                {"type": "string", "format": "uri", "description": "A URI"},
                [],  # No removals - supported format
                0,
            ),
            # additionalProperties constraints
            (
                "additionalProperties_true",
                {"type": "object", "additionalProperties": True},
                [],  # Not removed, but changed to false
                1,
            ),
            (
                "additionalProperties_false",
                {"type": "object", "additionalProperties": False},
                [],  # No changes - already false
                0,
            ),
            (
                "additionalProperties_schema",
                {"type": "object", "additionalProperties": {"type": "string"}},
                [],  # Not removed, but changed to false
                1,
            ),
            (
                "additionalProperties_missing",
                {"type": "object", "properties": {"name": {"type": "string"}}},
                [],  # Not removed, but additionalProperties added as false
                1,
            ),
            # Multiple constraint types together
            (
                "multiple_constraints",
                {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "minLength": 1, "maxLength": 100},
                        "age": {"type": "number", "minimum": 0, "maximum": 150},
                        "tags": {"type": "array", "minItems": 2, "uniqueItems": True},
                    },
                    "additionalProperties": True,
                },
                ["minLength", "maxLength", "minimum", "maximum", "uniqueItems"],
                7,  # 5 removals + 1 minItems reduction + 1 additionalProperties fix
            ),
        ]

        for test_name, schema, expected_removals, expected_changes_count in test_cases:
            with subtests.test(test_name=test_name):
                compatible, changes = preprocessor.make_compatible(schema)

                # Check that expected constraints were removed
                for constraint in expected_removals:
                    assert self._constraint_not_in_schema(compatible, constraint), (
                        f"{constraint} should be removed in {test_name}"
                    )

                # Check additionalProperties is set to false when present and not already false
                if "additionalProperties" in schema:
                    assert self._get_additional_properties_value(compatible) is False, (
                        f"additionalProperties should be false in {test_name}"
                    )

                # Check expected number of changes
                assert len(changes) == expected_changes_count, (
                    f"Expected {expected_changes_count} changes but got {len(changes)} in {test_name}: {changes}"
                )

    def test_nested_constraint_removal(self, preprocessor):
        """Test constraint removal in deeply nested schemas."""
        schema = {
            "type": "object",
            "properties": {
                "metadata": {
                    "type": "object",
                    "properties": {
                        "tags": {"type": "array", "uniqueItems": True, "minItems": 2},
                        "score": {"type": "number", "minimum": 0, "maximum": 100},
                        "name": {"type": "string", "minLength": 1, "maxLength": 50},
                    },
                    "additionalProperties": True,
                },
            },
        }

        compatible, changes = preprocessor.make_compatible(schema)

        # Check all nested constraints were fixed
        metadata_props = compatible["properties"]["metadata"]["properties"]
        assert "uniqueItems" not in metadata_props["tags"]
        assert metadata_props["tags"]["minItems"] == 1
        assert "minimum" not in metadata_props["score"]
        assert "maximum" not in metadata_props["score"]
        assert "minLength" not in metadata_props["name"]
        assert "maxLength" not in metadata_props["name"]
        assert compatible["properties"]["metadata"]["additionalProperties"] is False

        # Should have 6 changes: uniqueItems, minItems, minimum, maximum, minLength, maxLength, additionalProperties
        assert len(changes) == 7

    def _constraint_not_in_schema(self, schema: dict, constraint: str) -> bool:
        """Recursively check that a constraint is not present anywhere in schema."""
        if isinstance(schema, dict):
            if constraint in schema:
                return False
            for value in schema.values():
                if isinstance(value, dict):
                    if not self._constraint_not_in_schema(value, constraint):
                        return False
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            if not self._constraint_not_in_schema(item, constraint):
                                return False
        return True

    def _get_additional_properties_value(self, schema: dict) -> any:
        """Get additionalProperties value from schema, recursively checking nested objects."""
        if isinstance(schema, dict):
            if "additionalProperties" in schema:
                return schema["additionalProperties"]
            for value in schema.values():
                if isinstance(value, dict):
                    result = self._get_additional_properties_value(value)
                    if result is not None:
                        return result
        return None

    def test_detects_recursive_schemas(self, preprocessor):
        """Test that recursive schema references are detected."""
        schema = {
            "$defs": {
                "Criterion": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "subCriterion": {
                            "type": "array",
                            "items": {"$ref": "#/$defs/Criterion"},
                        },
                    },
                }
            }
        }

        compatible, changes = preprocessor.make_compatible(schema)

        # Should detect and fix the recursion
        assert len(changes) == 1
        assert "flattened recursive references" in changes[0]
        assert "Criterion" in changes[0]

    def test_flattens_criterion_schema(self, preprocessor):
        """Test flattening of the real Criterion schema from assembly specs."""
        schema = {
            "$defs": {
                "Criterion": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "subCriterion": {
                            "type": "array",
                            "items": {"$ref": "#/$defs/Criterion"},
                        },
                    },
                }
            }
        }

        compatible, changes = preprocessor.make_compatible(schema)

        # Check that recursion was removed
        criterion_def = compatible["$defs"]["Criterion"]
        sub_criterion = criterion_def["properties"]["subCriterion"]["items"]

        # Should no longer have a $ref to itself
        assert "$ref" not in sub_criterion
        # Should preserve the full object structure at depth limit
        assert sub_criterion["type"] == "object"
        # Should have the original properties (minus recursive ones)
        assert "id" in sub_criterion["properties"]
        assert "name" in sub_criterion["properties"]

    def test_no_changes_for_non_recursive_schemas(self, preprocessor):
        """Test that non-recursive schemas are left unchanged."""
        schema = {
            "$defs": {
                "Simple": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                    },
                }
            }
        }

        compatible, changes = preprocessor.make_compatible(schema)

        # No changes should be made
        assert len(changes) == 0
        assert compatible == schema
