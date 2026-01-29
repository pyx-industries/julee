"""
PointableJSONSchema utility for generating standalone schemas from JSON pointer targets.

This module provides the PointableJSONSchema class that handles the complexity of
extracting targeted schema sections while preserving important root metadata needed
for proper JSON Schema validation and structured outputs.
"""

from typing import Any, Dict

from jsonpointer import JsonPointer


class PointableJSONSchema:
    """Utility for generating standalone schemas from JSON pointer targets.

    This class takes a complete root schema and provides methods to generate
    standalone schemas for specific JSON pointer targets, preserving important
    root metadata like $schema, $id, definitions, etc.
    """

    def __init__(self, root_schema: Dict[str, Any]) -> None:
        """Initialize with the complete root schema.

        Args:
            root_schema: Complete JSON schema with all metadata and definitions
        """
        self.root_schema = root_schema

    def schema_for_pointer(self, json_pointer: str) -> Dict[str, Any]:
        """Generate a standalone schema for the given JSON pointer target.

        This method extracts the target schema section using the JSON pointer
        and builds a complete, standalone schema that preserves important root
        metadata while making the pointer target the main content structure.

        Args:
            json_pointer: JSON pointer string (e.g., "/properties/title")

        Returns:
            Complete standalone schema with preserved metadata, suitable for
            structured outputs or standalone validation

        Raises:
            ValueError: If JSON pointer is invalid or cannot be resolved
        """
        # Start with a copy of the root schema to preserve all metadata
        standalone_schema = self.root_schema.copy()

        # Handle empty pointer (refers to entire schema)
        if not json_pointer or json_pointer == "":
            return standalone_schema

        # Resolve the JSON pointer to get target schema
        try:
            pointer = JsonPointer(json_pointer)
            target_schema = pointer.resolve(self.root_schema)
        except Exception as e:
            raise ValueError(f"Invalid JSON pointer '{json_pointer}': {e}")

        # Ensure it's an object type and has additionalProperties set
        standalone_schema["type"] = "object"
        standalone_schema["additionalProperties"] = False

        # Enhance title to show which section this is (if title exists)
        if "title" in standalone_schema:
            standalone_schema["title"] = (
                f"{standalone_schema['title']} - {json_pointer}"
            )

        # Extract property name from JSON pointer (e.g., "/properties/title" -> "title")
        property_name = self._extract_property_name_from_pointer(json_pointer)

        # Handle special case for "properties" - use target directly as properties
        if property_name == "properties":
            standalone_schema["properties"] = target_schema
        else:
            # Replace properties with just the target property
            standalone_schema["properties"] = {property_name: target_schema}
            standalone_schema["required"] = [property_name]

        return standalone_schema

    def _extract_property_name_from_pointer(self, json_pointer: str) -> str:
        """Extract the final property name from a JSON pointer.

        Examples:
            "/properties/title" -> "title"
            "/properties/user/properties/name" -> "name"
            "/items" -> "items"
        """
        # Split pointer and get the last segment
        segments = json_pointer.strip("/").split("/")
        if len(segments) >= 2 and segments[-2] == "properties":
            # Standard case: "/properties/something" -> "something"
            return segments[-1]
        elif len(segments) >= 1:
            # Other cases: use the last segment
            return segments[-1]
        else:
            # Fallback for edge cases
            return "result"
