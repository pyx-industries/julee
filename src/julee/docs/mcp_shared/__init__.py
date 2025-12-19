"""Shared utilities for MCP servers.

This module provides common functionality used across HCD and C4 MCP servers:
- annotations: Tool annotation factories for consistent behavioral hints
- pagination: Result pagination utilities (P1)
- response_format: Response verbosity control (P1)
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

__all__ = [
    "read_only_annotation",
    "create_annotation",
    "update_annotation",
    "delete_annotation",
    "diagram_annotation",
]
