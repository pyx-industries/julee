"""Suggestion computation use-cases.

Computes contextual suggestions for entities based on domain semantics
and cross-entity validation rules.
"""

from dataclasses import dataclass

from julee.hcd.entities.accelerator import Accelerator
from julee.hcd.entities.app import App
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.integration import Integration
from julee.hcd.entities.journey import Journey, StepType
from julee.hcd.entities.persona import Persona
from julee.hcd.entities.story import Story
from julee.hcd.repositories.accelerator import AcceleratorRepository
from julee.hcd.repositories.app import AppRepository
from julee.hcd.repositories.epic import EpicRepository
from julee.hcd.repositories.integration import IntegrationRepository
from julee.hcd.repositories.journey import JourneyRepository
from julee.hcd.repositories.story import StoryRepository
from julee.hcd.utils import normalize_name

__all__ = ["SuggestionRepositories"]


@dataclass
class SuggestionRepositories:
    """Repository aggregate for suggestion computation.

    Groups all repositories needed by suggestion computation functions,
    replacing the SuggestionContextService abstraction with direct
    repository access.
    """

    stories: StoryRepository
    epics: EpicRepository
    journeys: JourneyRepository
    apps: AppRepository
    accelerators: AcceleratorRepository
    integrations: IntegrationRepository


async def compute_story_suggestions(
    story: Story, repos: SuggestionRepositories
) -> list[dict]:
    """Compute suggestions for a story.

    Returns list of suggestion dicts ready for MCP response.
    """
    from ....hcd_api.suggestions import (
        list_related_entities,
        story_has_unknown_persona,
        story_not_in_any_epic,
        story_persona_has_no_journey,
        story_references_unknown_app,
    )

    suggestions = []

    # Check persona
    if story.persona_normalized == "unknown":
        suggestions.append(story_has_unknown_persona(story.slug).model_dump())

    # Check app exists
    app_slugs = await repos.apps.list_slugs()
    if story.app_slug and story.app_slug not in app_slugs:
        suggestions.append(
            story_references_unknown_app(story.slug, story.app_slug).model_dump()
        )

    # Check if in any epic
    epics_with_story = await repos.epics.get_with_story_ref(story.feature_title)
    if not epics_with_story:
        all_epics = await repos.epics.list_all()
        available_epic_slugs = [e.slug for e in all_epics]
        suggestions.append(
            story_not_in_any_epic(
                story.slug, story.feature_title, available_epic_slugs
            ).model_dump()
        )
    else:
        # Info about related epics
        suggestions.append(
            list_related_entities(
                "story", story.slug, "epic", [e.slug for e in epics_with_story]
            ).model_dump()
        )

    # Check if persona has journeys
    if story.persona_normalized != "unknown":
        journeys = await repos.journeys.get_by_persona(story.persona)
        if not journeys:
            suggestions.append(
                story_persona_has_no_journey(story.slug, story.persona, []).model_dump()
            )
        else:
            # Info about related journeys
            suggestions.append(
                list_related_entities(
                    "story", story.slug, "journey", [j.slug for j in journeys]
                ).model_dump()
            )

    return suggestions


async def compute_epic_suggestions(
    epic: Epic, repos: SuggestionRepositories
) -> list[dict]:
    """Compute suggestions for an epic."""
    from ....hcd_api.suggestions import (
        epic_has_no_stories,
        epic_references_unknown_story,
        list_related_entities,
    )

    suggestions = []

    # Check if epic has stories
    if not epic.story_refs:
        suggestions.append(epic_has_no_stories(epic.slug).model_dump())
    else:
        # Check each story ref
        story_titles = await repos.stories.get_title_map()
        all_story_titles = list(story_titles.keys())

        for ref in epic.story_refs:
            normalized_ref = normalize_name(ref)
            if normalized_ref not in story_titles:
                # Find similar stories
                similar = [
                    t
                    for t in all_story_titles
                    if normalized_ref in t or t in normalized_ref
                ][:5]
                suggestions.append(
                    epic_references_unknown_story(epic.slug, ref, similar).model_dump()
                )

        # Info about matched stories
        matched_stories = [
            story_titles[normalize_name(ref)].slug
            for ref in epic.story_refs
            if normalize_name(ref) in story_titles
        ]
        if matched_stories:
            suggestions.append(
                list_related_entities(
                    "epic", epic.slug, "story", matched_stories
                ).model_dump()
            )

    return suggestions


async def compute_journey_suggestions(
    journey: Journey, repos: SuggestionRepositories
) -> list[dict]:
    """Compute suggestions for a journey."""
    from ....hcd_api.suggestions import (
        journey_depends_on_unknown,
        journey_has_no_steps,
        journey_persona_not_in_stories,
        journey_step_references_unknown_epic,
        journey_step_references_unknown_story,
    )

    suggestions = []

    # Check if journey has steps
    if not journey.steps:
        suggestions.append(
            journey_has_no_steps(journey.slug, journey.persona).model_dump()
        )
    else:
        # Check step references
        story_titles = await repos.stories.get_title_map()
        epic_slugs = await repos.epics.list_slugs()

        for step in journey.steps:
            if step.step_type == StepType.STORY:
                normalized_ref = normalize_name(step.ref)
                if normalized_ref not in story_titles:
                    all_titles = list(story_titles.keys())
                    suggestions.append(
                        journey_step_references_unknown_story(
                            journey.slug, step.ref, all_titles[:10]
                        ).model_dump()
                    )
            elif step.step_type == StepType.EPIC:
                if step.ref not in epic_slugs:
                    suggestions.append(
                        journey_step_references_unknown_epic(
                            journey.slug, step.ref, list(epic_slugs)[:10]
                        ).model_dump()
                    )

    # Check depends_on
    journey_slugs = await repos.journeys.list_slugs()
    for dep in journey.depends_on:
        if dep not in journey_slugs:
            suggestions.append(
                journey_depends_on_unknown(
                    journey.slug, dep, list(journey_slugs)[:10]
                ).model_dump()
            )

    # Check persona exists in stories
    personas = await repos.stories.get_all_personas()
    if journey.persona_normalized and journey.persona_normalized not in personas:
        suggestions.append(
            journey_persona_not_in_stories(
                journey.slug, journey.persona, list(personas)[:10]
            ).model_dump()
        )

    return suggestions


async def compute_accelerator_suggestions(
    accelerator: Accelerator, repos: SuggestionRepositories
) -> list[dict]:
    """Compute suggestions for an accelerator."""
    from ....hcd_api.suggestions import (
        accelerator_depends_on_unknown,
        accelerator_feeds_unknown,
        accelerator_has_no_integrations,
        accelerator_references_unknown_integration,
        list_related_entities,
    )

    suggestions = []

    # Check if has integrations
    if not accelerator.sources_from and not accelerator.publishes_to:
        suggestions.append(
            accelerator_has_no_integrations(accelerator.slug).model_dump()
        )
    else:
        # Check integration references
        integration_slugs = await repos.integrations.list_slugs()
        all_integrations = list(integration_slugs)

        for ref in accelerator.sources_from:
            if ref.slug not in integration_slugs:
                suggestions.append(
                    accelerator_references_unknown_integration(
                        accelerator.slug,
                        ref.slug,
                        "sources from",
                        all_integrations[:10],
                    ).model_dump()
                )

        for ref in accelerator.publishes_to:
            if ref.slug not in integration_slugs:
                suggestions.append(
                    accelerator_references_unknown_integration(
                        accelerator.slug,
                        ref.slug,
                        "publishes to",
                        all_integrations[:10],
                    ).model_dump()
                )

    # Check depends_on
    accelerator_slugs = await repos.accelerators.list_slugs()
    all_accelerators = list(accelerator_slugs)

    for dep in accelerator.depends_on:
        if dep not in accelerator_slugs:
            suggestions.append(
                accelerator_depends_on_unknown(
                    accelerator.slug, dep, all_accelerators[:10]
                ).model_dump()
            )

    for target in accelerator.feeds_into:
        if target not in accelerator_slugs:
            suggestions.append(
                accelerator_feeds_unknown(
                    accelerator.slug, target, all_accelerators[:10]
                ).model_dump()
            )

    # Info about apps using this accelerator
    apps = await repos.apps.get_by_accelerator(accelerator.slug)
    if apps:
        suggestions.append(
            list_related_entities(
                "accelerator", accelerator.slug, "app", [a.slug for a in apps]
            ).model_dump()
        )

    return suggestions


async def compute_integration_suggestions(
    integration: Integration, repos: SuggestionRepositories
) -> list[dict]:
    """Compute suggestions for an integration."""
    from ....hcd_api.suggestions import (
        integration_not_used_by_accelerators,
        list_related_entities,
    )

    suggestions = []

    # Check if used by any accelerators (sources from OR publishes to)
    sources_from = await repos.accelerators.get_by_integration(
        integration.slug, "sources_from"
    )
    publishes_to = await repos.accelerators.get_by_integration(
        integration.slug, "publishes_to"
    )
    # Combine and deduplicate
    accelerator_slugs_seen: set[str] = set()
    accelerators: list[Accelerator] = []
    for acc in sources_from + publishes_to:
        if acc.slug not in accelerator_slugs_seen:
            accelerator_slugs_seen.add(acc.slug)
            accelerators.append(acc)

    if not accelerators:
        suggestions.append(
            integration_not_used_by_accelerators(
                integration.slug, integration.name
            ).model_dump()
        )
    else:
        suggestions.append(
            list_related_entities(
                "integration",
                integration.slug,
                "accelerator",
                [a.slug for a in accelerators],
            ).model_dump()
        )

    return suggestions


async def compute_app_suggestions(
    app: App, repos: SuggestionRepositories
) -> list[dict]:
    """Compute suggestions for an app."""
    from ....hcd_api.suggestions import (
        app_has_no_stories,
        app_references_unknown_accelerator,
        list_related_entities,
    )

    suggestions = []

    # Check if app has stories
    stories = await repos.stories.get_by_app(app.slug)
    if not stories:
        suggestions.append(app_has_no_stories(app.slug, app.name).model_dump())
    else:
        suggestions.append(
            list_related_entities(
                "app", app.slug, "story", [s.slug for s in stories]
            ).model_dump()
        )

        # Info about personas
        personas = list(
            {s.persona for s in stories if s.persona_normalized != "unknown"}
        )
        if personas:
            suggestions.append(
                list_related_entities("app", app.slug, "persona", personas).model_dump()
            )

    # Check accelerator references
    accelerator_slugs = await repos.accelerators.list_slugs()
    for acc_slug in app.accelerators:
        if acc_slug not in accelerator_slugs:
            suggestions.append(
                app_references_unknown_accelerator(
                    app.slug, acc_slug, list(accelerator_slugs)[:10]
                ).model_dump()
            )

    return suggestions


async def compute_persona_suggestions(
    persona: Persona, repos: SuggestionRepositories
) -> list[dict]:
    """Compute suggestions for a persona."""
    from ....hcd_api.suggestions import (
        list_related_entities,
        persona_has_stories_but_no_journeys,
    )

    suggestions = []

    # Check if persona has journeys
    journeys = await repos.journeys.get_by_persona(persona.name)
    if not journeys and persona.app_slugs:
        suggestions.append(
            persona_has_stories_but_no_journeys(
                persona.name, len(persona.app_slugs), persona.app_slugs
            ).model_dump()
        )

    if journeys:
        suggestions.append(
            list_related_entities(
                "persona", persona.name, "journey", [j.slug for j in journeys]
            ).model_dump()
        )

    # Info about apps
    if persona.app_slugs:
        suggestions.append(
            list_related_entities(
                "persona", persona.name, "app", persona.app_slugs
            ).model_dump()
        )

    # Info about epics
    if persona.epic_slugs:
        suggestions.append(
            list_related_entities(
                "persona", persona.name, "epic", persona.epic_slugs
            ).model_dump()
        )

    return suggestions
