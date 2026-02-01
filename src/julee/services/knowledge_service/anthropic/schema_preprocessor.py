"""
Schema preprocessor for Anthropic structured outputs compatibility.

This module provides utilities to transform JSON schemas to be compatible
with Anthropic's structured outputs API, which has certain limitations
compared to full JSON Schema specification.

For full details on limitations, see:
https://platform.claude.com/docs/en/build-with-claude/structured-outputs#json-schema-limitations
"""

import copy
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AnthropicSchemaPreprocessor:
    """
    Preprocessor to make JSON schemas compatible with Anthropic structured outputs.

    Anthropic's structured outputs implementation has certain limitations:
    - minItems only supports values 0 or 1 (not 2, 3, etc.)
    - prefixItems is not supported at all
    - uniqueItems is not supported for array types
    - Numerical constraints (minimum, maximum, multipleOf, etc.) are not supported
    - String constraints (minLength, maxLength) are not supported
    - additionalProperties must be false (not true or a schema)
    - Recursive schemas are not supported (self-referencing definitions)
    - Other constraints may be discovered in the future

    This preprocessor transforms schemas to work around these limitations
    while preserving as much validation intent as possible.
    """

    def make_compatible(
        self, schema: dict[str, Any]
    ) -> tuple[dict[str, Any], list[str]]:
        """
        Transform schema to be compatible with Anthropic structured outputs.

        Args:
            schema: Original JSON schema dictionary

        Returns:
            Tuple of (compatible_schema, list_of_changes)
            - compatible_schema: Modified schema that works with Anthropic
            - list_of_changes: Human-readable list of changes made

        Example:
            >>> preprocessor = AnthropicSchemaPreprocessor()
            >>> original = {"type": "string", "minLength": 5, "maxLength": 10}
            >>> compatible, changes = preprocessor.make_compatible(original)
            >>> print(changes)
            ['minLength: removed (not supported by Anthropic)',
             'maxLength: removed (not supported by Anthropic)']
        """
        try:
            # Quick scan to see if we need to make any changes
            if not self._needs_processing(schema):
                return schema, []

            # Make deep copy only if changes are needed
            compatible_schema = copy.deepcopy(schema)
            changes: list[str] = []

            # Process the schema recursively
            self._process_schema_recursively(compatible_schema, "", changes)

            if changes:
                logger.info(
                    f"Schema modified for Anthropic compatibility: {len(changes)} changes made"
                )
                for change in changes:
                    logger.debug(f"Schema change: {change}")

            return compatible_schema, changes

        except Exception as e:
            logger.warning(
                f"Schema preprocessing failed: {e}. Using original schema.",
                exc_info=True,
            )
            return schema, []

    def _needs_processing(self, schema: dict[str, Any]) -> bool:
        """
        Quick scan to determine if schema needs processing.

        Returns True if any unsupported constraints found anywhere in schema.
        """
        if isinstance(schema, dict):
            # Check current level for all unsupported constraints
            if schema.get("minItems", 0) > 1:
                return True

            # Array constraints
            if (
                "prefixItems" in schema
                or "uniqueItems" in schema
                or self._has_contains_in_array_schema(schema)
            ):
                return True

            # String format constraints
            if self._has_unsupported_string_format(schema):
                return True

            # Numerical constraints
            numerical_constraints = {
                "minimum",
                "maximum",
                "multipleOf",
                "exclusiveMinimum",
                "exclusiveMaximum",
            }
            if any(constraint in schema for constraint in numerical_constraints):
                return True

            # String constraints
            if "minLength" in schema or "maxLength" in schema:
                return True

            # additionalProperties constraint - object schemas need explicit false
            is_object_schema = schema.get("type") == "object" or "properties" in schema
            if is_object_schema and schema.get("additionalProperties") is not False:
                return True

            # Check for recursive schema definitions
            if self._has_recursive_definitions(schema):
                return True

            # Check all nested values
            for value in schema.values():
                if isinstance(value, dict) and self._needs_processing(value):
                    return True
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and self._needs_processing(item):
                            return True

        return False

    def _process_schema_recursively(
        self, schema: dict[str, Any], path: str, changes: list[str]
    ) -> None:
        """
        Recursively process schema to fix incompatibilities.

        Args:
            schema: Schema dictionary to modify in-place
            path: JSON path for tracking location of changes
            changes: List to accumulate change descriptions
        """
        if not isinstance(schema, dict):
            return

        # Fix constraints at current level
        self._fix_min_items_constraint(schema, path, changes)
        self._fix_prefix_items_constraint(schema, path, changes)
        self._fix_unique_items_constraint(schema, path, changes)
        self._fix_contains_constraint(schema, path, changes)
        self._fix_numerical_constraints(schema, path, changes)
        self._fix_string_constraints(schema, path, changes)
        self._fix_string_format_constraints(schema, path, changes)
        self._fix_additional_properties_constraint(schema, path, changes)
        self._fix_recursive_schemas(schema, path, changes)

        # Process nested schemas
        for key, value in schema.items():
            current_path = f"{path}.{key}" if path else key

            if isinstance(value, dict):
                self._process_schema_recursively(value, current_path, changes)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        item_path = f"{current_path}[{i}]"
                        self._process_schema_recursively(item, item_path, changes)

    def _fix_min_items_constraint(
        self, schema: dict[str, Any], path: str, changes: list[str]
    ) -> None:
        """
        Fix minItems values that are incompatible with Anthropic.

        Anthropic only supports minItems values of 0 or 1.
        Values > 1 are reduced to 1.

        Args:
            schema: Schema dictionary to modify in-place
            path: JSON path for tracking location of change
            changes: List to accumulate change descriptions
        """
        min_items = schema.get("minItems")

        if isinstance(min_items, int) and min_items > 1:
            original_value = min_items
            schema["minItems"] = 1

            location = path if path else "root"
            change_msg = (
                f"{location}.minItems: reduced from {original_value} to 1 "
                f"(max supported by Anthropic)"
            )
            changes.append(change_msg)

    def _fix_prefix_items_constraint(
        self, schema: dict[str, Any], path: str, changes: list[str]
    ) -> None:
        """
        Fix prefixItems constraint that is incompatible with Anthropic.

        Anthropic does not support prefixItems. We remove it and use a
        generic items schema if needed.

        Args:
            schema: Schema dictionary to modify in-place
            path: JSON path for tracking location of change
            changes: List to accumulate change descriptions
        """
        if "prefixItems" in schema:
            prefix_items = schema.pop("prefixItems")

            # If there's no existing items constraint, create a generic one
            if (
                "items" not in schema
                and isinstance(prefix_items, list)
                and prefix_items
            ):
                # Use the first prefixItem as a generic items schema
                schema["items"] = prefix_items[0]

            location = path if path else "root"
            change_msg = f"{location}.prefixItems: removed (not supported by Anthropic)"
            changes.append(change_msg)

    def _fix_unique_items_constraint(
        self, schema: dict[str, Any], path: str, changes: list[str]
    ) -> None:
        """
        Fix uniqueItems constraint that is incompatible with Anthropic.

        Anthropic does not support uniqueItems for array types. We remove it
        entirely as it's a validation constraint that can't be enforced.

        Args:
            schema: Schema dictionary to modify in-place
            path: JSON path for tracking location of change
            changes: List to accumulate change descriptions
        """
        if "uniqueItems" in schema:
            schema.pop("uniqueItems")

            location = path if path else "root"
            change_msg = f"{location}.uniqueItems: removed (not supported by Anthropic)"
            changes.append(change_msg)

    def _fix_contains_constraint(
        self, schema: dict[str, Any], path: str, changes: list[str]
    ) -> None:
        """
        Fix contains constraint that is incompatible with Anthropic.

        Anthropic does not support 'contains' property for array types. We remove it
        from array schemas as it's a validation constraint that can't be enforced.
        This handles both direct contains and nested contains in allOf/anyOf/oneOf.

        Args:
            schema: Schema dictionary to modify in-place
            path: JSON path for tracking location of change
            changes: List to accumulate change descriptions
        """
        # Check if this is an array schema (explicit type or has items property)
        is_array_schema = schema.get("type") == "array" or "items" in schema

        if is_array_schema:
            # Remove direct contains property
            if "contains" in schema:
                schema.pop("contains")
                location = path if path else "root"
                change_msg = f"{location}.contains: removed (not supported by Anthropic for array types)"
                changes.append(change_msg)

            # Remove contains from nested combinators
            for combinator in ["allOf", "anyOf", "oneOf"]:
                if combinator in schema and isinstance(schema[combinator], list):
                    for i, sub_schema in enumerate(schema[combinator]):
                        if isinstance(sub_schema, dict) and "contains" in sub_schema:
                            sub_schema.pop("contains")
                            location = path if path else "root"
                            change_msg = f"{location}.{combinator}[{i}].contains: removed (not supported by Anthropic for array types)"
                            changes.append(change_msg)

    def _fix_numerical_constraints(
        self, schema: dict[str, Any], path: str, changes: list[str]
    ) -> None:
        """
        Fix numerical constraints that are incompatible with Anthropic.

        Anthropic does not support numerical validation constraints.
        We remove them entirely.

        Args:
            schema: Schema dictionary to modify in-place
            path: JSON path for tracking location of change
            changes: List to accumulate change descriptions
        """
        numerical_constraints = [
            "minimum",
            "maximum",
            "multipleOf",
            "exclusiveMinimum",
            "exclusiveMaximum",
        ]
        location = path if path else "root"

        for constraint in numerical_constraints:
            if constraint in schema:
                schema.pop(constraint)
                change_msg = (
                    f"{location}.{constraint}: removed (not supported by Anthropic)"
                )
                changes.append(change_msg)

    def _fix_string_constraints(
        self, schema: dict[str, Any], path: str, changes: list[str]
    ) -> None:
        """
        Fix string length constraints that are incompatible with Anthropic.

        Anthropic does not support minLength or maxLength constraints.
        We remove them entirely.

        Args:
            schema: Schema dictionary to modify in-place
            path: JSON path for tracking location of change
            changes: List to accumulate change descriptions
        """
        string_constraints = ["minLength", "maxLength"]
        location = path if path else "root"

        for constraint in string_constraints:
            if constraint in schema:
                schema.pop(constraint)
                change_msg = (
                    f"{location}.{constraint}: removed (not supported by Anthropic)"
                )
                changes.append(change_msg)

    def _fix_string_format_constraints(
        self, schema: dict[str, Any], path: str, changes: list[str]
    ) -> None:
        """
        Fix string format constraints that are incompatible with Anthropic.

        Anthropic does not support certain string formats like 'binary'.
        We remove unsupported formats entirely.

        Args:
            schema: Schema dictionary to modify in-place
            path: JSON path for tracking location of change
            changes: List to accumulate change descriptions
        """
        # List of string formats not supported by Anthropic
        unsupported_formats = ["binary"]

        if (
            schema.get("type") == "string"
            and "format" in schema
            and schema["format"] in unsupported_formats
        ):
            removed_format = schema.pop("format")
            location = path if path else "root"
            change_msg = f"{location}.format: removed '{removed_format}' (not supported by Anthropic)"
            changes.append(change_msg)

    def _fix_additional_properties_constraint(
        self, schema: dict[str, Any], path: str, changes: list[str]
    ) -> None:
        """
        Fix additionalProperties constraint that is incompatible with Anthropic.

        Anthropic requires all object schemas to explicitly have additionalProperties: false.
        We add or set it to false for all object schemas.

        Args:
            schema: Schema dictionary to modify in-place
            path: JSON path for tracking location of change
            changes: List to accumulate change descriptions
        """
        # Check if this is an object schema (explicit type or has properties)
        is_object_schema = schema.get("type") == "object" or "properties" in schema

        if is_object_schema and schema.get("additionalProperties") is not False:
            schema["additionalProperties"] = False
            location = path if path else "root"
            change_msg = f"{location}.additionalProperties: set to false (required by Anthropic for object types)"
            changes.append(change_msg)

    def _has_recursive_definitions(self, schema: dict[str, Any]) -> bool:
        """
        Check if schema contains recursive definitions.

        Returns True if any $defs or definitions contain self-references.
        """
        definitions = schema.get("$defs", schema.get("definitions", {}))
        if not definitions:
            return False

        for def_name, definition in definitions.items():
            if self._has_self_reference(definition, def_name, set()):
                return True
        return False

    def _has_self_reference(
        self, schema_part: dict[str, Any], target_ref: str, visited: set[str]
    ) -> bool:
        """
        Recursively check if a schema part references the target definition.

        Uses visited set to detect cycles and avoid infinite recursion.
        """
        if not isinstance(schema_part, dict):
            return False

        # Check if this part directly references our target
        ref = schema_part.get("$ref", "")
        if ref:
            # Extract definition name from $ref (e.g., "#/$defs/Criterion" -> "Criterion")
            ref_name = ref.split("/")[-1]
            if ref_name == target_ref:
                return True
            # Avoid infinite recursion when following references
            if ref_name in visited:
                return False
            visited.add(ref_name)

        # Recursively check all nested objects and arrays
        for value in schema_part.values():
            if isinstance(value, dict):
                if self._has_self_reference(value, target_ref, visited.copy()):
                    return True
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        if self._has_self_reference(item, target_ref, visited.copy()):
                            return True

        return False

    def _fix_recursive_schemas(
        self, schema: dict[str, Any], path: str, changes: list[str]
    ) -> None:
        """
        Fix recursive schema definitions by flattening to maximum 3 levels.

        Anthropic does not support recursive schemas. We flatten them by:
        1. Detecting self-referencing definitions
        2. Replacing recursive references with inline flattened structures
        3. Limiting depth to 3 levels, then simplifying to primitive types

        Args:
            schema: Schema dictionary to modify in-place
            path: JSON path for tracking location of change
            changes: List to accumulate change descriptions
        """
        definitions = schema.get("$defs", schema.get("definitions"))
        if not definitions:
            return

        definitions_key = "$defs" if "$defs" in schema else "definitions"
        location = f"{path}.{definitions_key}" if path else definitions_key

        for def_name, definition in list(definitions.items()):
            if self._has_self_reference(definition, def_name, set()):
                # Flatten the recursive definition
                flattened = self._flatten_recursive_definition(
                    definition, def_name, max_depth=3
                )
                definitions[def_name] = flattened

                change_msg = f"{location}.{def_name}: flattened recursive references to 3 levels (not supported by Anthropic)"
                changes.append(change_msg)

    def _flatten_recursive_definition(
        self, definition: dict[str, Any], target_ref: str, max_depth: int
    ) -> dict[str, Any]:
        """
        Flatten a recursive definition to a specified maximum depth.

        Args:
            definition: The schema definition to flatten
            target_ref: The name of the definition being flattened
            max_depth: Maximum levels of recursion to preserve

        Returns:
            Flattened schema definition
        """
        return self._flatten_recursive_part(
            definition, target_ref, max_depth, 0, definition
        )

    def _flatten_recursive_part(
        self,
        schema_part: dict[str, Any],
        target_ref: str,
        max_depth: int,
        current_depth: int,
        original_definition: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Recursively flatten a part of a schema.

        When we encounter a self-reference:
        - If depth < max_depth: inline the definition and continue
        - If depth >= max_depth: use full original definition but remove recursive properties
        """
        if not isinstance(schema_part, dict):
            return schema_part

        result = {}

        for key, value in schema_part.items():
            if key == "$ref":
                ref_name = value.split("/")[-1]
                if ref_name == target_ref:
                    if current_depth >= max_depth:
                        # At max depth, use full original definition but remove recursive properties
                        result = self._get_original_without_recursion(
                            original_definition, target_ref
                        )
                    else:
                        # Below max depth, inline the definition and continue flattening
                        result = self._flatten_recursive_part(
                            original_definition,
                            target_ref,
                            max_depth,
                            current_depth + 1,
                            original_definition,
                        )
                else:
                    # Different reference, keep as-is
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = self._flatten_recursive_part(
                    value, target_ref, max_depth, current_depth, original_definition
                )
            elif isinstance(value, list):
                result[key] = [
                    self._flatten_recursive_part(
                        item, target_ref, max_depth, current_depth, original_definition
                    )
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def _get_original_without_recursion(
        self, original_definition: dict[str, Any], target_ref: str
    ) -> dict[str, Any]:
        """
        Get the original definition but with recursive references removed.

        This preserves all the real properties of the object but removes
        any properties that contain recursive references to itself.
        """
        result = {}

        for key, value in original_definition.items():
            if isinstance(value, dict):
                # Check if this property contains a recursive reference
                if not self._contains_recursive_ref(value, target_ref):
                    result[key] = value
                # If it does contain recursion, skip it entirely
            elif isinstance(value, list):
                # For arrays, check if any items contain recursive references
                if not any(
                    self._contains_recursive_ref(item, target_ref)
                    if isinstance(item, dict)
                    else False
                    for item in value
                ):
                    result[key] = value
            else:
                # Primitive values are always safe
                result[key] = value

        return result

    def _contains_recursive_ref(
        self, schema_part: dict[str, Any], target_ref: str
    ) -> bool:
        """Check if a schema part contains a recursive reference to target_ref."""
        if isinstance(schema_part, dict):
            # Direct $ref check
            ref = schema_part.get("$ref", "")
            if ref and ref.split("/")[-1] == target_ref:
                return True

            # Check nested structures
            for value in schema_part.values():
                if isinstance(value, dict):
                    if self._contains_recursive_ref(value, target_ref):
                        return True
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and self._contains_recursive_ref(
                            item, target_ref
                        ):
                            return True

        return False

    def _has_unsupported_string_format(self, schema: dict[str, Any]) -> bool:
        """Check if schema has unsupported string format."""
        unsupported_formats = ["binary"]

        return (
            schema.get("type") == "string"
            and "format" in schema
            and schema["format"] in unsupported_formats
        )

    def _has_contains_in_array_schema(self, schema: dict[str, Any]) -> bool:
        """Check if schema has contains property and is an array schema."""
        # Check if this is an array schema (explicit type or has items property)
        is_array_schema = schema.get("type") == "array" or "items" in schema

        if not is_array_schema:
            return False

        # Check direct contains
        if "contains" in schema:
            return True

        # Check contains in nested combinators
        for combinator in ["allOf", "anyOf", "oneOf"]:
            if combinator in schema and isinstance(schema[combinator], list):
                for sub_schema in schema[combinator]:
                    if isinstance(sub_schema, dict) and "contains" in sub_schema:
                        return True

        return False
