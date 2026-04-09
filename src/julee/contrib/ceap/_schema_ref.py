"""
Shared helpers for resolving JSON Schema $ref values.

A bare $ref schema is a dict of exactly {"$ref": "url#/fragment"}.
Resolution means fetching the URL and, if a fragment is present,
navigating to the target sub-schema and bundling the parent $defs so
that internal $ref values within the sub-schema remain valid.
"""

from typing import Any

import jsonpointer  # type: ignore


def extract_schema_from_fetched(
    full_schema: dict[str, Any], fragment: str
) -> dict[str, Any]:
    """Return the sub-schema identified by *fragment* from *full_schema*.

    If *fragment* is empty the full schema is returned as-is.  Otherwise the
    fragment is treated as a JSON Pointer; the target object is extracted and
    the parent ``$defs`` are merged in so that any internal ``$ref`` values
    within the sub-schema continue to resolve correctly.
    """
    if not fragment:
        return full_schema

    target = jsonpointer.resolve_pointer(full_schema, fragment)
    if not isinstance(target, dict):
        raise ValueError(f"$ref fragment '{fragment}' did not resolve to a JSON object")
    result = dict(target)
    parent_defs = full_schema.get("$defs", {})
    if parent_defs:
        result["$defs"] = {**parent_defs, **result.get("$defs", {})}
    return result
