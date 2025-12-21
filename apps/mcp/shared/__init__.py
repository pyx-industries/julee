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
from .error_handling import (
    ErrorType,
    conflict_error,
    find_similar,
    not_found_error,
    permission_error,
    reference_error,
    validation_error,
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
from .response_models import (
    ErrorInfo,
    MCPGetResponse,
    MCPListResponse,
    MCPMutationResponse,
    PaginationInfo,
    SuggestionInfo,
    get_response,
    list_response,
    mutation_response,
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
    # Response models
    "MCPGetResponse",
    "MCPListResponse",
    "MCPMutationResponse",
    "PaginationInfo",
    "SuggestionInfo",
    "ErrorInfo",
    "get_response",
    "list_response",
    "mutation_response",
    # Error handling
    "ErrorType",
    "not_found_error",
    "validation_error",
    "conflict_error",
    "reference_error",
    "permission_error",
    "find_similar",
]
