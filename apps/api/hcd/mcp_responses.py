"""Enhanced MCP response types with contextual suggestions.

These response types wrap domain entities with rich contextual guidance
to help agents understand the current state and suggested next actions.
"""

from typing import Any

from pydantic import BaseModel, Field

from .suggestions import Suggestion


class MCPEntityResponse(BaseModel):
    """Base response for a single entity with suggestions."""

    entity: dict[str, Any] | None = Field(description="The entity data as a dictionary")
    found: bool = Field(
        default=True, description="Whether the entity was found (for get operations)"
    )
    suggestions: list[Suggestion] = Field(
        default_factory=list,
        description="Contextual suggestions based on domain semantics",
    )

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warning-level suggestions."""
        return any(s.severity.value in ("warning", "error") for s in self.suggestions)


class MCPListResponse(BaseModel):
    """Base response for a list of entities with suggestions."""

    entities: list[dict[str, Any]] = Field(
        default_factory=list, description="List of entity data as dictionaries"
    )
    count: int = Field(default=0, description="Number of entities returned")
    suggestions: list[Suggestion] = Field(
        default_factory=list, description="Global suggestions for the entity collection"
    )

    def model_post_init(self, __context: Any) -> None:
        """Compute count from entities if not set."""
        if self.count == 0 and self.entities:
            object.__setattr__(self, "count", len(self.entities))


class MCPMutationResponse(BaseModel):
    """Response for create/update/delete operations with suggestions."""

    success: bool = Field(description="Whether the operation succeeded")
    entity: dict[str, Any] | None = Field(
        default=None, description="The created/updated entity (None for delete)"
    )
    suggestions: list[Suggestion] = Field(
        default_factory=list,
        description="Suggestions for next steps after this operation",
    )


# =============================================================================
# Story Responses
# =============================================================================


class MCPStoryResponse(MCPEntityResponse):
    """Response for getting a story with contextual suggestions.

    Suggestions may include:
    - Warning if persona is 'unknown'
    - Warning if app doesn't exist
    - Suggestion to add story to an epic if not in any
    - Suggestion to create a journey for the persona
    - Info about related epics and journeys
    """

    pass


class MCPStoriesResponse(MCPListResponse):
    """Response for listing stories with suggestions.

    Suggestions may include:
    - Warnings about stories with unknown personas
    - Info about persona distribution
    - Suggestions for orphaned stories (not in any epic)
    """

    pass


class MCPStoryMutationResponse(MCPMutationResponse):
    """Response for story create/update/delete with next step suggestions."""

    pass


# =============================================================================
# Epic Responses
# =============================================================================


class MCPEpicResponse(MCPEntityResponse):
    """Response for getting an epic with contextual suggestions.

    Suggestions may include:
    - Warning if epic has no stories
    - Warnings for story_refs that don't match any stories
    - Info about related journeys
    """

    pass


class MCPEpicsResponse(MCPListResponse):
    """Response for listing epics with suggestions."""

    pass


class MCPEpicMutationResponse(MCPMutationResponse):
    """Response for epic create/update/delete with next step suggestions."""

    pass


# =============================================================================
# Journey Responses
# =============================================================================


class MCPJourneyResponse(MCPEntityResponse):
    """Response for getting a journey with contextual suggestions.

    Suggestions may include:
    - Warning if journey has no steps
    - Warnings for steps referencing non-existent stories/epics
    - Warning if depends_on references non-existent journeys
    - Warning if persona doesn't match any story personas
    """

    pass


class MCPJourneysResponse(MCPListResponse):
    """Response for listing journeys with suggestions."""

    pass


class MCPJourneyMutationResponse(MCPMutationResponse):
    """Response for journey create/update/delete with next step suggestions."""

    pass


# =============================================================================
# Accelerator Responses
# =============================================================================


class MCPAcceleratorResponse(MCPEntityResponse):
    """Response for getting an accelerator with contextual suggestions.

    Suggestions may include:
    - Suggestion if no integrations defined
    - Warnings for references to non-existent integrations
    - Warnings for depends_on/feeds_into non-existent accelerators
    - Info about related apps
    """

    pass


class MCPAcceleratorsResponse(MCPListResponse):
    """Response for listing accelerators with suggestions."""

    pass


class MCPAcceleratorMutationResponse(MCPMutationResponse):
    """Response for accelerator create/update/delete with next step suggestions."""

    pass


# =============================================================================
# Integration Responses
# =============================================================================


class MCPIntegrationResponse(MCPEntityResponse):
    """Response for getting an integration with contextual suggestions.

    Suggestions may include:
    - Info if not used by any accelerators
    - Info about accelerators that use this integration
    """

    pass


class MCPIntegrationsResponse(MCPListResponse):
    """Response for listing integrations with suggestions."""

    pass


class MCPIntegrationMutationResponse(MCPMutationResponse):
    """Response for integration create/update/delete with next step suggestions."""

    pass


# =============================================================================
# App Responses
# =============================================================================


class MCPAppResponse(MCPEntityResponse):
    """Response for getting an app with contextual suggestions.

    Suggestions may include:
    - Suggestion if app has no stories
    - Warnings for references to non-existent accelerators
    - Info about stories in this app
    - Info about personas using this app
    """

    pass


class MCPAppsResponse(MCPListResponse):
    """Response for listing apps with suggestions."""

    pass


class MCPAppMutationResponse(MCPMutationResponse):
    """Response for app create/update/delete with next step suggestions."""

    pass


# =============================================================================
# Persona Responses
# =============================================================================


class MCPPersonaResponse(MCPEntityResponse):
    """Response for getting a persona with contextual suggestions.

    Suggestions may include:
    - Suggestion to create journeys if persona has stories but no journeys
    - Info about apps this persona uses
    - Info about epics this persona participates in
    """

    pass


class MCPPersonasResponse(MCPListResponse):
    """Response for listing personas with suggestions.

    Suggestions may include:
    - Info about personas without journeys
    """

    pass
