"""Shared utilities for MCP servers.

This module provides common functionality used across HCD and C4 MCP servers:
- annotations: Tool annotation factories for consistent behavioral hints
- pagination: Result pagination utilities
- response_format: Response verbosity control
- response_models: Pydantic response schemas (P2)
- error_handling: Structured error responses (P2)
"""

from .annotations import (
    create_annotation,
    delete_annotation,
    diagram_annotation,
    read_only_annotation,
    update_annotation,
)
from .pagination import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    paginate_results,
)
from .response_format import (
    ResponseFormat,
    format_entities,
    format_entity,
)

__all__ = [
    # Annotations
    "read_only_annotation",
    "create_annotation",
    "update_annotation",
    "delete_annotation",
    "diagram_annotation",
    # Pagination
    "paginate_results",
    "DEFAULT_LIMIT",
    "MAX_LIMIT",
    # Response format
    "ResponseFormat",
    "format_entity",
    "format_entities",
]
