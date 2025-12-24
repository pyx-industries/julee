"""Pydantic response models for MCP server responses.

Provides type-safe, validated response structures for consistent API responses.
These models define the contract between MCP tools and their callers.

Usage:
    from apps.mcp.shared import MCPGetResponse, MCPListResponse

    @mcp.tool()
    async def mcp_get_story(slug: str) -> dict:
        story = await get_story(slug)
        return MCPGetResponse(
            entity=story.model_dump(),
            found=True,
        ).model_dump()
"""

from typing import Any

from pydantic import BaseModel, Field


class PaginationInfo(BaseModel):
    """Pagination metadata for list responses."""

    total: int = Field(description="Total number of items available")
    limit: int = Field(description="Maximum items per page")
    offset: int = Field(description="Number of items skipped")
    has_more: bool = Field(description="Whether more items exist beyond this page")


class SuggestionInfo(BaseModel):
    """Contextual suggestion for agent guidance.

    Suggestions help agents understand next steps, potential issues,
    and related operations they might want to perform.
    """

    severity: str = Field(
        description="Importance level: 'info', 'suggestion', 'warning', 'error'"
    )
    category: str = Field(
        description="Suggestion type: 'incomplete', 'orphan', 'next_step', etc."
    )
    message: str = Field(description="Human-readable description of the suggestion")
    action: str = Field(description="Recommended action to take")
    tool: str | None = Field(default=None, description="Suggested tool to call")
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context for the action"
    )


class ErrorInfo(BaseModel):
    """Structured error information for failed operations.

    Provides consistent error reporting with suggestions for resolution.
    """

    type: str = Field(description="Error type: 'NOT_FOUND', 'VALIDATION', 'CONFLICT'")
    message: str = Field(description="Human-readable error description")
    field: str | None = Field(default=None, description="Field that caused the error")
    similar: list[str] = Field(
        default_factory=list,
        description="Similar existing items (for typo suggestions)",
    )


class MCPGetResponse(BaseModel):
    """Response model for single-entity get operations.

    Used by: get_story, get_epic, get_software_system, etc.
    """

    entity: dict[str, Any] | None = Field(
        description="The requested entity, or None if not found"
    )
    found: bool = Field(description="Whether the entity was found")
    suggestions: list[SuggestionInfo] = Field(
        default_factory=list, description="Contextual suggestions"
    )
    error: ErrorInfo | None = Field(
        default=None, description="Error details if operation failed"
    )


class MCPListResponse(BaseModel):
    """Response model for list operations with pagination.

    Used by: list_stories, list_containers, etc.
    """

    entities: list[dict[str, Any]] = Field(description="List of entities")
    count: int = Field(description="Number of entities in this response")
    pagination: PaginationInfo = Field(description="Pagination metadata")
    suggestions: list[SuggestionInfo] = Field(
        default_factory=list, description="Aggregate suggestions"
    )
    efficiency_hint: str | None = Field(
        default=None, description="Hint for large result sets"
    )


class MCPMutationResponse(BaseModel):
    """Response model for create/update/delete operations.

    Used by: create_story, update_container, delete_epic, etc.
    """

    success: bool = Field(description="Whether the operation succeeded")
    entity: dict[str, Any] | None = Field(
        description="The created/updated entity, or None for deletes"
    )
    suggestions: list[SuggestionInfo] = Field(
        default_factory=list, description="Follow-up suggestions"
    )
    error: ErrorInfo | None = Field(
        default=None, description="Error details if operation failed"
    )


# Convenience functions for building responses


def get_response(
    entity: dict[str, Any] | None,
    found: bool,
    suggestions: list[dict[str, Any]] | None = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a standardized get response.

    Args:
        entity: The entity dict or None
        found: Whether the entity was found
        suggestions: List of suggestion dicts
        error: Error info dict

    Returns:
        Response dict matching MCPGetResponse schema
    """
    response = MCPGetResponse(
        entity=entity,
        found=found,
        suggestions=[SuggestionInfo(**s) for s in (suggestions or [])],
        error=ErrorInfo(**error) if error else None,
    )
    return response.model_dump(exclude_none=True)


def list_response(
    entities: list[dict[str, Any]],
    pagination: dict[str, Any],
    suggestions: list[dict[str, Any]] | None = None,
    efficiency_hint: str | None = None,
) -> dict[str, Any]:
    """Build a standardized list response.

    Args:
        entities: List of entity dicts
        pagination: Pagination info dict
        suggestions: List of suggestion dicts
        efficiency_hint: Optional efficiency hint

    Returns:
        Response dict matching MCPListResponse schema
    """
    response = MCPListResponse(
        entities=entities,
        count=len(entities),
        pagination=PaginationInfo(**pagination),
        suggestions=[SuggestionInfo(**s) for s in (suggestions or [])],
        efficiency_hint=efficiency_hint,
    )
    return response.model_dump(exclude_none=True)


def mutation_response(
    success: bool,
    entity: dict[str, Any] | None = None,
    suggestions: list[dict[str, Any]] | None = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a standardized mutation response.

    Args:
        success: Whether the operation succeeded
        entity: The entity dict or None
        suggestions: List of suggestion dicts
        error: Error info dict

    Returns:
        Response dict matching MCPMutationResponse schema
    """
    response = MCPMutationResponse(
        success=success,
        entity=entity,
        suggestions=[SuggestionInfo(**s) for s in (suggestions or [])],
        error=ErrorInfo(**error) if error else None,
    )
    return response.model_dump(exclude_none=True)
