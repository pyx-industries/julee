"""
Unit tests for PointableJSONSchema utility class.

These tests verify that the PointableJSONSchema class correctly generates
standalone schemas from JSON pointer targets while preserving important
root metadata needed for proper JSON Schema validation.
"""

import pytest

from julee.domain.use_cases.pointable_json_schema import PointableJSONSchema


class TestPointableJSONSchema:
    """Test cases for PointableJSONSchema class."""

    def test_simple_property_extraction(self) -> None:
        """Test extracting a simple property schema."""
        root_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "count": {"type": "integer"},
            },
            "required": ["title"],
        }

        pointable = PointableJSONSchema(root_schema)
        result = pointable.schema_for_pointer("/properties/title")

        expected = {
            "type": "object",
            "properties": {"title": {"type": "string"}},
            "required": ["title"],
            "additionalProperties": False,
        }
        assert result == expected

    def test_complex_property_extraction(self) -> None:
        """Test extracting a complex property schema."""
        root_schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                    "required": ["name"],
                },
            },
        }

        pointable = PointableJSONSchema(root_schema)
        result = pointable.schema_for_pointer("/properties/user")

        expected = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                    "required": ["name"],
                }
            },
            "required": ["user"],
            "additionalProperties": False,
        }
        assert result == expected

    def test_primitive_value_wrapping(self) -> None:
        """Test that primitive values are used directly with proper property name."""
        root_schema = {
            "type": "object",
            "properties": {
                "title": "some string value",  # Not a proper schema
            },
        }

        pointable = PointableJSONSchema(root_schema)
        result = pointable.schema_for_pointer("/properties/title")

        expected = {
            "type": "object",
            "properties": {"title": "some string value"},
            "required": ["title"],
            "additionalProperties": False,
        }
        assert result == expected

    def test_preserves_schema_metadata(self) -> None:
        """Test that important root metadata is preserved."""
        root_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://example.com/schema.json",
            "title": "Test Schema",
            "description": "A test schema for validation",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
        }

        pointable = PointableJSONSchema(root_schema)
        result = pointable.schema_for_pointer("/properties/name")

        expected = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://example.com/schema.json",
            "title": "Test Schema - /properties/name",
            "description": "A test schema for validation",
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        }
        assert result == expected

    def test_preserves_definitions(self) -> None:
        """Test that definitions are preserved for $ref resolution."""
        root_schema = {
            "type": "object",
            "definitions": {
                "timestamp": {"type": "string", "format": "date-time"},
                "person": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                },
            },
            "properties": {
                "created_at": {"$ref": "#/definitions/timestamp"},
                "author": {"$ref": "#/definitions/person"},
            },
        }

        pointable = PointableJSONSchema(root_schema)
        result = pointable.schema_for_pointer("/properties/created_at")

        expected = {
            "type": "object",
            "additionalProperties": False,
            "definitions": {
                "timestamp": {"type": "string", "format": "date-time"},
                "person": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                },
            },
            "properties": {"created_at": {"$ref": "#/definitions/timestamp"}},
            "required": ["created_at"],
        }
        assert result == expected

    def test_preserves_defs(self) -> None:
        """Test that $defs (newer JSON Schema) are preserved."""
        root_schema = {
            "type": "object",
            "$defs": {
                "timestamp": {"type": "string", "format": "date-time"},
            },
            "properties": {
                "created_at": {"$ref": "#/$defs/timestamp"},
            },
        }

        pointable = PointableJSONSchema(root_schema)
        result = pointable.schema_for_pointer("/properties/created_at")

        expected = {
            "type": "object",
            "additionalProperties": False,
            "$defs": {
                "timestamp": {"type": "string", "format": "date-time"},
            },
            "properties": {"created_at": {"$ref": "#/$defs/timestamp"}},
            "required": ["created_at"],
        }
        assert result == expected

    def test_empty_pointer_returns_root_schema(self) -> None:
        """Test that empty pointer returns the complete root schema."""
        root_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
            },
        }

        pointable = PointableJSONSchema(root_schema)
        result = pointable.schema_for_pointer("")

        assert result == root_schema

    def test_nested_pointer_extraction(self) -> None:
        """Test extracting deeply nested properties."""
        root_schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {
                                "email": {"type": "string", "format": "email"},
                            },
                        },
                    },
                },
            },
        }

        pointable = PointableJSONSchema(root_schema)
        result = pointable.schema_for_pointer("/properties/user/properties/profile")

        expected = {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                    },
                }
            },
            "required": ["profile"],
            "additionalProperties": False,
        }
        assert result == expected

    def test_invalid_pointer_raises_error(self) -> None:
        """Test that invalid JSON pointers raise ValueError."""
        root_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
            },
        }

        pointable = PointableJSONSchema(root_schema)

        with pytest.raises(ValueError, match="Invalid JSON pointer"):
            pointable.schema_for_pointer("/properties/nonexistent")

    def test_malformed_pointer_raises_error(self) -> None:
        """Test that malformed JSON pointers raise ValueError."""
        root_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
            },
        }

        pointable = PointableJSONSchema(root_schema)

        with pytest.raises(ValueError, match="Invalid JSON pointer"):
            pointable.schema_for_pointer("not/a/valid/pointer")

    def test_array_items_extraction(self) -> None:
        """Test extracting array item schemas."""
        root_schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        }

        pointable = PointableJSONSchema(root_schema)
        result = pointable.schema_for_pointer("/properties/tags/items")

        expected = {
            "type": "object",
            "properties": {"items": {"type": "string"}},
            "required": ["items"],
            "additionalProperties": False,
        }
        assert result == expected

    def test_preserves_all_metadata(self) -> None:
        """Test that all root metadata is preserved."""
        root_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://example.com/schema.json",
            "title": "Test Schema",
            "description": "A test schema",
            "version": "1.0.0",  # This should not be preserved
            "custom_field": "value",  # This should not be preserved
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
        }

        pointable = PointableJSONSchema(root_schema)
        result = pointable.schema_for_pointer("/properties/name")

        # Should preserve all root metadata
        expected = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://example.com/schema.json",
            "title": "Test Schema - /properties/name",
            "description": "A test schema",
            "version": "1.0.0",
            "custom_field": "value",
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        }
        assert result == expected

    def test_handles_schema_without_metadata(self) -> None:
        """Test schemas that don't have any root metadata."""
        root_schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer"},
            },
        }

        pointable = PointableJSONSchema(root_schema)
        result = pointable.schema_for_pointer("/properties/count")

        expected = {
            "type": "object",
            "properties": {"count": {"type": "integer"}},
            "required": ["count"],
            "additionalProperties": False,
        }
        assert result == expected

    def test_properties_pointer_extraction(self) -> None:
        """Test extracting the entire properties object - this reveals the double-wrapping issue."""
        root_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "type": ["DigitalProductPassport", "VerifiableCredential"],
                "@context": [
                    "https://www.w3.org/ns/credentials/v2",
                    "https://test.uncefact.org/vocabulary/untp/dpp/0.6.0/",
                ],
                "id": "https://bondor.com.au/credentials/bondorpanel-dpp-2024",
                "issuer": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                    },
                },
            },
            "required": ["type", "@context", "id", "issuer"],
        }

        pointable = PointableJSONSchema(root_schema)
        result = pointable.schema_for_pointer("/properties")

        # This should return a schema that validates the properties DIRECTLY,
        # NOT wrapped in another "properties" object
        expected = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "type": ["DigitalProductPassport", "VerifiableCredential"],
                "@context": [
                    "https://www.w3.org/ns/credentials/v2",
                    "https://test.uncefact.org/vocabulary/untp/dpp/0.6.0/",
                ],
                "id": "https://bondor.com.au/credentials/bondorpanel-dpp-2024",
                "issuer": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                    },
                },
            },
            "required": ["type", "@context", "id", "issuer"],
        }
        assert result == expected

    def test_complex_schema_with_all_features(self) -> None:
        """Test a complex schema with multiple features."""
        root_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://example.com/assembly-spec.json",
            "title": "Production Assembly Specification",
            "description": "Schema for production data assembly",
            "definitions": {
                "timestamp": {"type": "string", "format": "date-time"},
                "person": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "id": {"type": "string"},
                    },
                    "required": ["name", "id"],
                },
            },
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "created_at": {"$ref": "#/definitions/timestamp"},
                "author": {"$ref": "#/definitions/person"},
                "metadata": {
                    "type": "object",
                    "properties": {
                        "version": {"type": "string"},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            },
            "required": ["title", "created_at", "author"],
        }

        pointable = PointableJSONSchema(root_schema)
        result = pointable.schema_for_pointer("/properties/author")

        expected = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://example.com/assembly-spec.json",
            "title": "Production Assembly Specification - /properties/author",
            "description": "Schema for production data assembly",
            "definitions": {
                "timestamp": {"type": "string", "format": "date-time"},
                "person": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "id": {"type": "string"},
                    },
                    "required": ["name", "id"],
                },
            },
            "type": "object",
            "additionalProperties": False,
            "properties": {"author": {"$ref": "#/definitions/person"}},
            "required": ["author"],
        }
        assert result == expected
