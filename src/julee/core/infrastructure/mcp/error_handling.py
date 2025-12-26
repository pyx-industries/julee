"""Error handling utilities for MCP server responses.

Provides consistent error responses with helpful suggestions for resolution.
Errors include similar item suggestions for typos and guidance on next steps.

Usage:
    from julee.core.infrastructure.mcp import not_found_error, validation_error

    if not response.story:
        return not_found_error("story", slug, available_slugs)
"""

from difflib import SequenceMatcher
from typing import Any


class ErrorType:
    """Standard error type constants."""

    NOT_FOUND = "NOT_FOUND"
    VALIDATION = "VALIDATION"
    CONFLICT = "CONFLICT"
    REFERENCE = "REFERENCE"
    PERMISSION = "PERMISSION"


def find_similar(
    target: str,
    candidates: list[str],
    max_results: int = 3,
    threshold: float = 0.5,
) -> list[str]:
    """Find similar strings from candidates using fuzzy matching.

    Args:
        target: String to match against
        candidates: List of possible matches
        max_results: Maximum similar items to return
        threshold: Minimum similarity ratio (0-1)

    Returns:
        List of similar strings, sorted by similarity
    """
    if not target or not candidates:
        return []

    target_lower = target.lower()
    scored = []

    for candidate in candidates:
        ratio = SequenceMatcher(None, target_lower, candidate.lower()).ratio()
        if ratio >= threshold:
            scored.append((candidate, ratio))

    # Sort by similarity descending
    scored.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in scored[:max_results]]


def not_found_error(
    entity_type: str,
    identifier: str,
    available: list[str] | None = None,
) -> dict[str, Any]:
    """Build a not-found error response with similar suggestions.

    Args:
        entity_type: Type of entity (e.g., "story", "container")
        identifier: The identifier that wasn't found
        available: List of available identifiers for suggestions

    Returns:
        Error response dict with entity=None, found=False, and error details
    """
    similar = find_similar(identifier, available or [])

    error_info: dict[str, Any] = {
        "type": ErrorType.NOT_FOUND,
        "message": f"{entity_type.replace('_', ' ').title()} '{identifier}' not found",
    }

    if similar:
        error_info["similar"] = similar

    suggestions = []
    if similar:
        suggestions.append(
            {
                "severity": "info",
                "category": "typo_suggestion",
                "message": f"Did you mean: {', '.join(similar)}?",
                "action": f"Try one of the similar {entity_type} identifiers",
                "tool": f"get_{entity_type}",
                "context": {"similar_slugs": similar},
            }
        )
    else:
        suggestions.append(
            {
                "severity": "info",
                "category": "next_step",
                "message": f"No {entity_type.replace('_', ' ')} found with that identifier",
                "action": f"List all {entity_type.replace('_', ' ')}s to find the correct one",
                "tool": f"list_{entity_type}s",
                "context": {},
            }
        )

    return {
        "entity": None,
        "found": False,
        "error": error_info,
        "suggestions": suggestions,
    }


def validation_error(
    message: str,
    field: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a validation error response.

    Args:
        message: Description of the validation failure
        field: Field that failed validation (optional)
        details: Additional error details

    Returns:
        Error response dict
    """
    error_info: dict[str, Any] = {
        "type": ErrorType.VALIDATION,
        "message": message,
    }

    if field:
        error_info["field"] = field

    suggestions = [
        {
            "severity": "error",
            "category": "validation",
            "message": message,
            "action": "Review and correct the input",
            "tool": None,
            "context": details or {},
        }
    ]

    return {
        "success": False,
        "entity": None,
        "error": error_info,
        "suggestions": suggestions,
    }


def conflict_error(
    entity_type: str,
    identifier: str,
    conflict_type: str = "already exists",
) -> dict[str, Any]:
    """Build a conflict error response.

    Args:
        entity_type: Type of entity
        identifier: The conflicting identifier
        conflict_type: Description of the conflict

    Returns:
        Error response dict
    """
    error_info: dict[str, Any] = {
        "type": ErrorType.CONFLICT,
        "message": f"{entity_type.replace('_', ' ').title()} '{identifier}' {conflict_type}",
    }

    suggestions = [
        {
            "severity": "warning",
            "category": "conflict",
            "message": f"A {entity_type.replace('_', ' ')} with this identifier already exists",
            "action": f"Use update_{entity_type} to modify the existing entity, or choose a different identifier",
            "tool": f"update_{entity_type}",
            "context": {"existing_slug": identifier},
        }
    ]

    return {
        "success": False,
        "entity": None,
        "error": error_info,
        "suggestions": suggestions,
    }


def reference_error(
    entity_type: str,
    identifier: str,
    referenced_type: str,
    referenced_id: str,
    available: list[str] | None = None,
) -> dict[str, Any]:
    """Build a broken reference error response.

    Args:
        entity_type: Type of entity being created/updated
        identifier: The entity identifier
        referenced_type: Type of referenced entity that doesn't exist
        referenced_id: The missing reference identifier
        available: List of available reference identifiers

    Returns:
        Error response dict
    """
    similar = find_similar(referenced_id, available or [])

    error_info: dict[str, Any] = {
        "type": ErrorType.REFERENCE,
        "message": f"Referenced {referenced_type.replace('_', ' ')} '{referenced_id}' not found",
        "field": f"{referenced_type}_slug",
    }

    if similar:
        error_info["similar"] = similar

    suggestions = []
    if similar:
        suggestions.append(
            {
                "severity": "info",
                "category": "typo_suggestion",
                "message": f"Did you mean: {', '.join(similar)}?",
                "action": f"Check the {referenced_type.replace('_', ' ')} identifier",
                "tool": f"get_{referenced_type}",
                "context": {"similar_slugs": similar},
            }
        )

    suggestions.append(
        {
            "severity": "info",
            "category": "next_step",
            "message": f"Create the missing {referenced_type.replace('_', ' ')} first",
            "action": f"Use create_{referenced_type} to create it",
            "tool": f"create_{referenced_type}",
            "context": {"suggested_slug": referenced_id},
        }
    )

    return {
        "success": False,
        "entity": None,
        "error": error_info,
        "suggestions": suggestions,
    }


def permission_error(
    operation: str,
    entity_type: str,
    reason: str = "insufficient permissions",
) -> dict[str, Any]:
    """Build a permission error response.

    Args:
        operation: The attempted operation (e.g., "delete", "update")
        entity_type: Type of entity
        reason: Reason for denial

    Returns:
        Error response dict
    """
    error_info: dict[str, Any] = {
        "type": ErrorType.PERMISSION,
        "message": f"Cannot {operation} {entity_type.replace('_', ' ')}: {reason}",
    }

    suggestions = [
        {
            "severity": "error",
            "category": "permission",
            "message": f"The {operation} operation is not allowed",
            "action": "Check your permissions or contact an administrator",
            "tool": None,
            "context": {"operation": operation, "entity_type": entity_type},
        }
    ]

    return {
        "success": False,
        "entity": None,
        "error": error_info,
        "suggestions": suggestions,
    }
