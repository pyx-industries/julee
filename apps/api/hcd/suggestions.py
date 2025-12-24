"""Suggestion models for MCP contextual guidance.

Provides rich contextual cues to agents using HCD tools, suggesting next actions
based on domain semantics and validation rules.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SuggestionSeverity(str, Enum):
    """Severity level for suggestions."""

    INFO = "info"  # Helpful context, no action required
    SUGGESTION = "suggestion"  # Recommended action to improve completeness
    WARNING = "warning"  # Potential issue that should be addressed
    ERROR = "error"  # Invalid state that must be fixed


class SuggestionCategory(str, Enum):
    """Category of suggestion for filtering/grouping."""

    MISSING_REFERENCE = "missing_reference"  # Referenced entity doesn't exist
    ORPHAN = "orphan"  # Entity not referenced by anything
    INCOMPLETE = "incomplete"  # Entity missing recommended fields
    RELATIONSHIP = "relationship"  # Suggestion about entity relationships
    NEXT_STEP = "next_step"  # Suggested next action in workflow


class Suggestion(BaseModel):
    """A contextual suggestion for an agent.

    Provides actionable guidance based on domain semantics.
    """

    severity: SuggestionSeverity = Field(description="How urgent this suggestion is")
    category: SuggestionCategory = Field(description="Type of suggestion for filtering")
    message: str = Field(description="Human-readable explanation of the suggestion")
    action: str = Field(description="Recommended action to take")
    tool: str | None = Field(
        default=None,
        description="MCP tool name to use for the action (e.g., 'create_epic')",
    )
    context: dict[str, Any] = Field(
        default_factory=dict, description="Related entities or values for context"
    )


class EntitySuggestions(BaseModel):
    """Suggestions for a single entity."""

    entity_type: str = Field(description="Type of entity (story, epic, etc.)")
    entity_slug: str = Field(description="Slug of the entity")
    suggestions: list[Suggestion] = Field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Check if any suggestions are errors."""
        return any(s.severity == SuggestionSeverity.ERROR for s in self.suggestions)

    @property
    def has_warnings(self) -> bool:
        """Check if any suggestions are warnings."""
        return any(s.severity == SuggestionSeverity.WARNING for s in self.suggestions)


# =============================================================================
# Suggestion Builders - Factory functions for common suggestions
# =============================================================================


def story_has_unknown_persona(story_slug: str) -> Suggestion:
    """Suggest adding a persona to a story with 'unknown' persona."""
    return Suggestion(
        severity=SuggestionSeverity.WARNING,
        category=SuggestionCategory.INCOMPLETE,
        message="Story has no persona defined (defaulted to 'unknown')",
        action="Update the story to specify a persona in the 'As a <persona>' format",
        tool="update_story",
        context={"story_slug": story_slug, "field": "persona"},
    )


def story_references_unknown_app(story_slug: str, app_slug: str) -> Suggestion:
    """Warn that a story references a non-existent app."""
    return Suggestion(
        severity=SuggestionSeverity.WARNING,
        category=SuggestionCategory.MISSING_REFERENCE,
        message=f"Story references unknown app '{app_slug}'",
        action=f"Create the app '{app_slug}' or update the story to reference an existing app",
        tool="create_app",
        context={"story_slug": story_slug, "app_slug": app_slug},
    )


def story_not_in_any_epic(
    story_slug: str, feature_title: str, available_epics: list[str]
) -> Suggestion:
    """Suggest adding a story to an epic."""
    if available_epics:
        action = f"Add this story to an existing epic (available: {', '.join(available_epics[:5])}) or create a new epic"
    else:
        action = "Create an epic to group this story with related stories"
    return Suggestion(
        severity=SuggestionSeverity.SUGGESTION,
        category=SuggestionCategory.ORPHAN,
        message="Story is not included in any epic",
        action=action,
        tool="create_epic" if not available_epics else "update_epic",
        context={
            "story_slug": story_slug,
            "feature_title": feature_title,
            "available_epics": available_epics[:10],
        },
    )


def story_persona_has_no_journey(
    story_slug: str, persona: str, existing_journeys: list[str]
) -> Suggestion:
    """Suggest creating a journey for a persona that has stories but no journeys."""
    if existing_journeys:
        action = f"Add steps to an existing journey for this persona (available: {', '.join(existing_journeys[:5])})"
    else:
        action = f"Create a journey for persona '{persona}' that includes this story"
    return Suggestion(
        severity=SuggestionSeverity.SUGGESTION,
        category=SuggestionCategory.NEXT_STEP,
        message=f"Persona '{persona}' has no journey that includes this story",
        action=action,
        tool="create_journey" if not existing_journeys else "update_journey",
        context={
            "story_slug": story_slug,
            "persona": persona,
            "existing_journeys": existing_journeys[:10],
        },
    )


def epic_has_no_stories(epic_slug: str) -> Suggestion:
    """Suggest adding stories to an empty epic."""
    return Suggestion(
        severity=SuggestionSeverity.WARNING,
        category=SuggestionCategory.INCOMPLETE,
        message="Epic has no stories defined",
        action="Add story references to this epic using story feature titles",
        tool="update_epic",
        context={"epic_slug": epic_slug, "field": "story_refs"},
    )


def epic_references_unknown_story(
    epic_slug: str, story_ref: str, similar_stories: list[str]
) -> Suggestion:
    """Warn that an epic references a non-existent story."""
    if similar_stories:
        action = f"Check if you meant one of: {', '.join(similar_stories[:5])}"
    else:
        action = "Create the story or remove the invalid reference"
    return Suggestion(
        severity=SuggestionSeverity.WARNING,
        category=SuggestionCategory.MISSING_REFERENCE,
        message=f"Epic references unknown story '{story_ref}'",
        action=action,
        tool="create_story",
        context={
            "epic_slug": epic_slug,
            "story_ref": story_ref,
            "similar_stories": similar_stories[:5],
        },
    )


def journey_has_no_steps(journey_slug: str, persona: str) -> Suggestion:
    """Suggest defining steps for a journey."""
    return Suggestion(
        severity=SuggestionSeverity.WARNING,
        category=SuggestionCategory.INCOMPLETE,
        message="Journey has no steps defined",
        action=f"Define the sequence of steps (stories/epics/phases) that '{persona}' takes in this journey",
        tool="update_journey",
        context={"journey_slug": journey_slug, "field": "steps"},
    )


def journey_step_references_unknown_story(
    journey_slug: str, step_ref: str, available_stories: list[str]
) -> Suggestion:
    """Warn that a journey step references a non-existent story."""
    if available_stories:
        action = f"Reference an existing story (available: {', '.join(available_stories[:5])})"
    else:
        action = "Create the story first, then reference it in the journey step"
    return Suggestion(
        severity=SuggestionSeverity.WARNING,
        category=SuggestionCategory.MISSING_REFERENCE,
        message=f"Journey step references unknown story '{step_ref}'",
        action=action,
        tool="create_story",
        context={
            "journey_slug": journey_slug,
            "step_ref": step_ref,
            "available_stories": available_stories[:10],
        },
    )


def journey_step_references_unknown_epic(
    journey_slug: str, step_ref: str, available_epics: list[str]
) -> Suggestion:
    """Warn that a journey step references a non-existent epic."""
    if available_epics:
        action = (
            f"Reference an existing epic (available: {', '.join(available_epics[:5])})"
        )
    else:
        action = "Create the epic first, then reference it in the journey step"
    return Suggestion(
        severity=SuggestionSeverity.WARNING,
        category=SuggestionCategory.MISSING_REFERENCE,
        message=f"Journey step references unknown epic '{step_ref}'",
        action=action,
        tool="create_epic",
        context={
            "journey_slug": journey_slug,
            "step_ref": step_ref,
            "available_epics": available_epics[:10],
        },
    )


def journey_depends_on_unknown(
    journey_slug: str, dep_slug: str, available_journeys: list[str]
) -> Suggestion:
    """Warn that a journey depends on a non-existent journey."""
    return Suggestion(
        severity=SuggestionSeverity.WARNING,
        category=SuggestionCategory.MISSING_REFERENCE,
        message=f"Journey depends on unknown journey '{dep_slug}'",
        action=f"Create journey '{dep_slug}' or remove the dependency",
        tool="create_journey",
        context={
            "journey_slug": journey_slug,
            "dependency": dep_slug,
            "available_journeys": available_journeys[:10],
        },
    )


def journey_persona_not_in_stories(
    journey_slug: str, persona: str, available_personas: list[str]
) -> Suggestion:
    """Warn that a journey's persona doesn't match any story personas."""
    return Suggestion(
        severity=SuggestionSeverity.WARNING,
        category=SuggestionCategory.MISSING_REFERENCE,
        message=f"Journey persona '{persona}' doesn't match any story personas",
        action=f"Use an existing persona (available: {', '.join(available_personas[:5])}) or create stories for this persona",
        tool="create_story",
        context={
            "journey_slug": journey_slug,
            "persona": persona,
            "available_personas": available_personas[:10],
        },
    )


def accelerator_has_no_integrations(accelerator_slug: str) -> Suggestion:
    """Suggest defining integrations for an accelerator."""
    return Suggestion(
        severity=SuggestionSeverity.SUGGESTION,
        category=SuggestionCategory.INCOMPLETE,
        message="Accelerator has no source or publish integrations defined",
        action="Define which integrations this accelerator sources data from or publishes to",
        tool="update_accelerator",
        context={
            "accelerator_slug": accelerator_slug,
            "fields": ["sources_from", "publishes_to"],
        },
    )


def accelerator_references_unknown_integration(
    accelerator_slug: str,
    integration_slug: str,
    direction: str,
    available_integrations: list[str],
) -> Suggestion:
    """Warn that an accelerator references a non-existent integration."""
    return Suggestion(
        severity=SuggestionSeverity.WARNING,
        category=SuggestionCategory.MISSING_REFERENCE,
        message=f"Accelerator {direction} unknown integration '{integration_slug}'",
        action=f"Create integration '{integration_slug}' or use an existing one (available: {', '.join(available_integrations[:5])})",
        tool="create_integration",
        context={
            "accelerator_slug": accelerator_slug,
            "integration_slug": integration_slug,
            "direction": direction,
            "available_integrations": available_integrations[:10],
        },
    )


def accelerator_depends_on_unknown(
    accelerator_slug: str, dep_slug: str, available_accelerators: list[str]
) -> Suggestion:
    """Warn that an accelerator depends on a non-existent accelerator."""
    return Suggestion(
        severity=SuggestionSeverity.WARNING,
        category=SuggestionCategory.MISSING_REFERENCE,
        message=f"Accelerator depends on unknown accelerator '{dep_slug}'",
        action=f"Create accelerator '{dep_slug}' or use an existing one (available: {', '.join(available_accelerators[:5])})",
        tool="create_accelerator",
        context={
            "accelerator_slug": accelerator_slug,
            "dependency": dep_slug,
            "available_accelerators": available_accelerators[:10],
        },
    )


def accelerator_feeds_unknown(
    accelerator_slug: str, target_slug: str, available_accelerators: list[str]
) -> Suggestion:
    """Warn that an accelerator feeds into a non-existent accelerator."""
    return Suggestion(
        severity=SuggestionSeverity.WARNING,
        category=SuggestionCategory.MISSING_REFERENCE,
        message=f"Accelerator feeds into unknown accelerator '{target_slug}'",
        action=f"Create accelerator '{target_slug}' or use an existing one",
        tool="create_accelerator",
        context={
            "accelerator_slug": accelerator_slug,
            "target": target_slug,
            "available_accelerators": available_accelerators[:10],
        },
    )


def app_has_no_stories(app_slug: str, app_name: str) -> Suggestion:
    """Suggest creating stories for an app without any."""
    return Suggestion(
        severity=SuggestionSeverity.SUGGESTION,
        category=SuggestionCategory.INCOMPLETE,
        message=f"App '{app_name}' has no user stories",
        action=f"Create user stories that describe what personas can do with '{app_name}'",
        tool="create_story",
        context={"app_slug": app_slug, "app_name": app_name},
    )


def app_references_unknown_accelerator(
    app_slug: str, accelerator_slug: str, available_accelerators: list[str]
) -> Suggestion:
    """Warn that an app references a non-existent accelerator."""
    return Suggestion(
        severity=SuggestionSeverity.WARNING,
        category=SuggestionCategory.MISSING_REFERENCE,
        message=f"App references unknown accelerator '{accelerator_slug}'",
        action=f"Create accelerator '{accelerator_slug}' or use an existing one (available: {', '.join(available_accelerators[:5])})",
        tool="create_accelerator",
        context={
            "app_slug": app_slug,
            "accelerator_slug": accelerator_slug,
            "available_accelerators": available_accelerators[:10],
        },
    )


def integration_not_used_by_accelerators(
    integration_slug: str, integration_name: str
) -> Suggestion:
    """Info that an integration isn't used by any accelerators."""
    return Suggestion(
        severity=SuggestionSeverity.INFO,
        category=SuggestionCategory.ORPHAN,
        message=f"Integration '{integration_name}' is not referenced by any accelerators",
        action="Consider which accelerators source from or publish to this integration",
        tool="update_accelerator",
        context={"integration_slug": integration_slug},
    )


def persona_has_stories_but_no_journeys(
    persona_name: str, story_count: int, app_slugs: list[str]
) -> Suggestion:
    """Suggest creating journeys for a persona with stories but no journeys."""
    return Suggestion(
        severity=SuggestionSeverity.SUGGESTION,
        category=SuggestionCategory.NEXT_STEP,
        message=f"Persona '{persona_name}' has {story_count} stories but no journeys",
        action=f"Create a journey describing how '{persona_name}' accomplishes their goals across these apps",
        tool="create_journey",
        context={
            "persona": persona_name,
            "story_count": story_count,
            "apps": app_slugs[:10],
        },
    )


def list_related_entities(
    entity_type: str,
    entity_slug: str,
    related_type: str,
    related_slugs: list[str],
) -> Suggestion:
    """Info about related entities for context."""
    return Suggestion(
        severity=SuggestionSeverity.INFO,
        category=SuggestionCategory.RELATIONSHIP,
        message=f"This {entity_type} is related to {len(related_slugs)} {related_type}(s)",
        action=f"Review related {related_type}s if needed",
        tool=f"get_{related_type}",
        context={
            "entity_type": entity_type,
            "entity_slug": entity_slug,
            "related_type": related_type,
            "related_slugs": related_slugs[:20],
        },
    )
