"""Response format utilities for MCP server responses.

Controls response verbosity to optimize token usage. Agents can request
minimal data for listing operations, or full details when needed.

Usage:
    from apps.mcp.shared import ResponseFormat, format_entity

    @mcp.tool()
    async def mcp_get_story(slug: str, format: str = "full") -> dict:
        story = get_story(slug)
        return {
            "entity": format_entity(story.model_dump(), ResponseFormat(format), "story"),
            "found": True,
        }
"""

from enum import Enum
from typing import Any


class ResponseFormat(str, Enum):
    """Response verbosity levels.

    - SUMMARY: Essential fields only (~30-50 tokens per entity)
    - FULL: All entity fields (~100-200 tokens per entity)
    - EXTENDED: Full plus relationship data (~200-400 tokens per entity)
    """

    SUMMARY = "summary"
    FULL = "full"
    EXTENDED = "extended"

    @classmethod
    def from_string(cls, value: str | None) -> "ResponseFormat":
        """Convert string to ResponseFormat, defaulting to FULL."""
        if not value:
            return cls.FULL
        try:
            return cls(value.lower())
        except ValueError:
            return cls.FULL


# Entity type to summary fields mapping
# Summary includes slug + primary identifying field(s)
SUMMARY_FIELDS: dict[str, list[str]] = {
    # HCD entities
    "story": ["slug", "feature_title", "persona", "app_slug"],
    "epic": ["slug", "description"],
    "journey": ["slug", "persona", "goal"],
    "persona": ["slug", "name", "is_defined"],
    "app": ["slug", "name", "app_type"],
    "accelerator": ["slug", "status", "objective"],
    "integration": ["slug", "name", "direction"],
    # C4 entities
    "software_system": ["slug", "name", "system_type"],
    "container": ["slug", "name", "system_slug", "container_type"],
    "component": ["slug", "name", "container_slug"],
    "relationship": ["slug", "source_slug", "destination_slug", "description"],
    "deployment_node": ["slug", "name", "environment", "node_type"],
    "dynamic_step": ["slug", "sequence_name", "step_number", "description"],
}

# Fields to exclude from full responses (internal/computed fields)
EXCLUDE_FIELDS: set[str] = {
    "abs_path",
    "name_normalized",
    "persona_normalized",
    "app_normalized",
    "manifest_path",
}


def format_entity(
    entity: dict[str, Any],
    format: ResponseFormat | str,
    entity_type: str,
    relationships: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format an entity based on requested verbosity level.

    Args:
        entity: Full entity dict (from model_dump())
        format: Desired verbosity level
        entity_type: Type of entity for field selection (e.g., "story", "app")
        relationships: Optional relationship data for extended format

    Returns:
        Filtered entity dict based on format
    """
    if isinstance(format, str):
        format = ResponseFormat.from_string(format)

    if format == ResponseFormat.SUMMARY:
        summary_keys = SUMMARY_FIELDS.get(entity_type, ["slug", "name"])
        return {k: v for k, v in entity.items() if k in summary_keys}

    elif format == ResponseFormat.FULL:
        return {k: v for k, v in entity.items() if k not in EXCLUDE_FIELDS}

    else:  # EXTENDED
        result = {k: v for k, v in entity.items() if k not in EXCLUDE_FIELDS}
        if relationships:
            result["_relationships"] = relationships
        return result


def format_entities(
    entities: list[dict[str, Any]],
    format: ResponseFormat | str,
    entity_type: str,
) -> list[dict[str, Any]]:
    """Format a list of entities based on requested verbosity level.

    Args:
        entities: List of full entity dicts
        format: Desired verbosity level
        entity_type: Type of entities for field selection

    Returns:
        List of filtered entity dicts
    """
    return [format_entity(e, format, entity_type) for e in entities]


def get_format_param_description() -> str:
    """Return standard docstring text for format parameter.

    Use this to maintain consistent documentation across operations.
    """
    return """    format: Response verbosity - "summary" (essential fields), "full" (all fields), or "extended" (with relationships). Default: "full"."""
