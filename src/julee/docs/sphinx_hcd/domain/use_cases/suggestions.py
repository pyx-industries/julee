"""Suggestion computation use-cases.

Computes contextual suggestions for entities based on domain semantics
and cross-entity validation rules.
"""

from ...utils import normalize_name
from ..models.accelerator import Accelerator
from ..models.app import App
from ..models.epic import Epic
from ..models.integration import Integration
from ..models.journey import Journey, StepType
from ..models.persona import Persona
from ..models.story import Story
from ..repositories.accelerator import AcceleratorRepository
from ..repositories.app import AppRepository
from ..repositories.epic import EpicRepository
from ..repositories.integration import IntegrationRepository
from ..repositories.journey import JourneyRepository
from ..repositories.persona import PersonaRepository
from ..repositories.story import StoryRepository


class SuggestionContext:
    """Context for computing suggestions with access to all repositories.

    This provides the cross-entity visibility needed to compute meaningful
    suggestions based on domain relationships.
    """

    def __init__(
        self,
        story_repo: StoryRepository,
        epic_repo: EpicRepository,
        journey_repo: JourneyRepository,
        accelerator_repo: AcceleratorRepository,
        integration_repo: IntegrationRepository,
        app_repo: AppRepository,
        persona_repo: PersonaRepository | None = None,
    ) -> None:
        """Initialize with all repository dependencies."""
        self.story_repo = story_repo
        self.epic_repo = epic_repo
        self.journey_repo = journey_repo
        self.accelerator_repo = accelerator_repo
        self.integration_repo = integration_repo
        self.app_repo = app_repo
        self.persona_repo = persona_repo

        # Caches for computed data
        self._stories: list[Story] | None = None
        self._epics: list[Epic] | None = None
        self._journeys: list[Journey] | None = None
        self._accelerators: list[Accelerator] | None = None
        self._integrations: list[Integration] | None = None
        self._apps: list[App] | None = None
        self._defined_personas: list[Persona] | None = None

    async def get_all_stories(self) -> list[Story]:
        """Get all stories (cached)."""
        if self._stories is None:
            self._stories = await self.story_repo.list_all()
        return self._stories

    async def get_all_epics(self) -> list[Epic]:
        """Get all epics (cached)."""
        if self._epics is None:
            self._epics = await self.epic_repo.list_all()
        return self._epics

    async def get_all_journeys(self) -> list[Journey]:
        """Get all journeys (cached)."""
        if self._journeys is None:
            self._journeys = await self.journey_repo.list_all()
        return self._journeys

    async def get_all_accelerators(self) -> list[Accelerator]:
        """Get all accelerators (cached)."""
        if self._accelerators is None:
            self._accelerators = await self.accelerator_repo.list_all()
        return self._accelerators

    async def get_all_integrations(self) -> list[Integration]:
        """Get all integrations (cached)."""
        if self._integrations is None:
            self._integrations = await self.integration_repo.list_all()
        return self._integrations

    async def get_all_apps(self) -> list[App]:
        """Get all apps (cached)."""
        if self._apps is None:
            self._apps = await self.app_repo.list_all()
        return self._apps

    async def get_story_slugs(self) -> set[str]:
        """Get set of all story slugs."""
        stories = await self.get_all_stories()
        return {s.slug for s in stories}

    async def get_story_titles_normalized(self) -> dict[str, Story]:
        """Get mapping of normalized feature titles to stories."""
        stories = await self.get_all_stories()
        return {normalize_name(s.feature_title): s for s in stories}

    async def get_epic_slugs(self) -> set[str]:
        """Get set of all epic slugs."""
        epics = await self.get_all_epics()
        return {e.slug for e in epics}

    async def get_journey_slugs(self) -> set[str]:
        """Get set of all journey slugs."""
        journeys = await self.get_all_journeys()
        return {j.slug for j in journeys}

    async def get_accelerator_slugs(self) -> set[str]:
        """Get set of all accelerator slugs."""
        accelerators = await self.get_all_accelerators()
        return {a.slug for a in accelerators}

    async def get_integration_slugs(self) -> set[str]:
        """Get set of all integration slugs."""
        integrations = await self.get_all_integrations()
        return {i.slug for i in integrations}

    async def get_app_slugs(self) -> set[str]:
        """Get set of all app slugs."""
        apps = await self.get_all_apps()
        return {a.slug for a in apps}

    async def get_personas(self) -> set[str]:
        """Get set of all unique personas from stories."""
        stories = await self.get_all_stories()
        return {s.persona_normalized for s in stories if s.persona_normalized != "unknown"}

    async def get_defined_personas(self) -> list[Persona]:
        """Get all defined personas (cached)."""
        if self._defined_personas is None:
            if self.persona_repo is not None:
                self._defined_personas = await self.persona_repo.list_all()
            else:
                self._defined_personas = []
        return self._defined_personas

    async def get_defined_persona_names_normalized(self) -> dict[str, Persona]:
        """Get mapping of normalized persona names to defined personas."""
        defined = await self.get_defined_personas()
        return {p.normalized_name: p for p in defined}

    async def is_persona_defined(self, persona_name: str) -> bool:
        """Check if a persona name matches a defined persona."""
        defined_map = await self.get_defined_persona_names_normalized()
        return normalize_name(persona_name) in defined_map

    async def get_epics_containing_story(self, story_title: str) -> list[Epic]:
        """Find epics that reference a story by title."""
        epics = await self.get_all_epics()
        normalized = normalize_name(story_title)
        return [
            e for e in epics
            if any(normalize_name(ref) == normalized for ref in e.story_refs)
        ]

    async def get_journeys_for_persona(self, persona: str) -> list[Journey]:
        """Find journeys for a specific persona."""
        journeys = await self.get_all_journeys()
        normalized = normalize_name(persona)
        return [j for j in journeys if j.persona_normalized == normalized]

    async def get_stories_for_app(self, app_slug: str) -> list[Story]:
        """Find stories belonging to an app."""
        stories = await self.get_all_stories()
        return [s for s in stories if s.app_slug == app_slug]

    async def get_accelerators_using_integration(self, integration_slug: str) -> list[Accelerator]:
        """Find accelerators that source from or publish to an integration."""
        accelerators = await self.get_all_accelerators()
        return [
            a for a in accelerators
            if any(ref.slug == integration_slug for ref in a.sources_from)
            or any(ref.slug == integration_slug for ref in a.publishes_to)
        ]

    async def get_apps_using_accelerator(self, accelerator_slug: str) -> list[App]:
        """Find apps that reference an accelerator."""
        apps = await self.get_all_apps()
        return [a for a in apps if accelerator_slug in a.accelerators]


async def compute_story_suggestions(
    story: Story, ctx: SuggestionContext
) -> list[dict]:
    """Compute suggestions for a story.

    Returns list of suggestion dicts ready for MCP response.
    """
    from ....hcd_api.suggestions import (
        list_related_entities,
        story_has_unknown_persona,
        story_not_in_any_epic,
        story_persona_has_no_journey,
        story_references_undefined_persona,
        story_references_unknown_app,
    )

    suggestions = []

    # Check persona
    if story.persona_normalized == "unknown":
        suggestions.append(story_has_unknown_persona(story.slug).model_dump())
    else:
        # Check if persona is defined (reconciliation warning)
        is_defined = await ctx.is_persona_defined(story.persona)
        if not is_defined:
            defined_personas = await ctx.get_defined_personas()
            defined_names = [p.name for p in defined_personas]
            suggestions.append(
                story_references_undefined_persona(
                    story.slug, story.persona, defined_names
                ).model_dump()
            )

    # Check app exists
    app_slugs = await ctx.get_app_slugs()
    if story.app_slug and story.app_slug not in app_slugs:
        suggestions.append(
            story_references_unknown_app(story.slug, story.app_slug).model_dump()
        )

    # Check if in any epic
    epics_with_story = await ctx.get_epics_containing_story(story.feature_title)
    if not epics_with_story:
        all_epics = await ctx.get_all_epics()
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
        journeys = await ctx.get_journeys_for_persona(story.persona)
        if not journeys:
            suggestions.append(
                story_persona_has_no_journey(
                    story.slug, story.persona, []
                ).model_dump()
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
    epic: Epic, ctx: SuggestionContext
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
        story_titles = await ctx.get_story_titles_normalized()
        all_story_titles = list(story_titles.keys())

        for ref in epic.story_refs:
            normalized_ref = normalize_name(ref)
            if normalized_ref not in story_titles:
                # Find similar stories
                similar = [
                    t for t in all_story_titles
                    if normalized_ref in t or t in normalized_ref
                ][:5]
                suggestions.append(
                    epic_references_unknown_story(
                        epic.slug, ref, similar
                    ).model_dump()
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
    journey: Journey, ctx: SuggestionContext
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
        story_titles = await ctx.get_story_titles_normalized()
        epic_slugs = await ctx.get_epic_slugs()

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
    journey_slugs = await ctx.get_journey_slugs()
    for dep in journey.depends_on:
        if dep not in journey_slugs:
            suggestions.append(
                journey_depends_on_unknown(
                    journey.slug, dep, list(journey_slugs)[:10]
                ).model_dump()
            )

    # Check persona exists in stories
    personas = await ctx.get_personas()
    if journey.persona_normalized and journey.persona_normalized not in personas:
        suggestions.append(
            journey_persona_not_in_stories(
                journey.slug, journey.persona, list(personas)[:10]
            ).model_dump()
        )

    return suggestions


async def compute_accelerator_suggestions(
    accelerator: Accelerator, ctx: SuggestionContext
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
        integration_slugs = await ctx.get_integration_slugs()
        all_integrations = list(integration_slugs)

        for ref in accelerator.sources_from:
            if ref.slug not in integration_slugs:
                suggestions.append(
                    accelerator_references_unknown_integration(
                        accelerator.slug, ref.slug, "sources from", all_integrations[:10]
                    ).model_dump()
                )

        for ref in accelerator.publishes_to:
            if ref.slug not in integration_slugs:
                suggestions.append(
                    accelerator_references_unknown_integration(
                        accelerator.slug, ref.slug, "publishes to", all_integrations[:10]
                    ).model_dump()
                )

    # Check depends_on
    accelerator_slugs = await ctx.get_accelerator_slugs()
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
    apps = await ctx.get_apps_using_accelerator(accelerator.slug)
    if apps:
        suggestions.append(
            list_related_entities(
                "accelerator", accelerator.slug, "app", [a.slug for a in apps]
            ).model_dump()
        )

    return suggestions


async def compute_integration_suggestions(
    integration: Integration, ctx: SuggestionContext
) -> list[dict]:
    """Compute suggestions for an integration."""
    from ....hcd_api.suggestions import (
        integration_not_used_by_accelerators,
        list_related_entities,
    )

    suggestions = []

    # Check if used by any accelerators
    accelerators = await ctx.get_accelerators_using_integration(integration.slug)
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
    app: App, ctx: SuggestionContext
) -> list[dict]:
    """Compute suggestions for an app."""
    from ....hcd_api.suggestions import (
        app_has_no_stories,
        app_references_unknown_accelerator,
        list_related_entities,
    )

    suggestions = []

    # Check if app has stories
    stories = await ctx.get_stories_for_app(app.slug)
    if not stories:
        suggestions.append(
            app_has_no_stories(app.slug, app.name).model_dump()
        )
    else:
        suggestions.append(
            list_related_entities(
                "app", app.slug, "story", [s.slug for s in stories]
            ).model_dump()
        )

        # Info about personas
        personas = list({s.persona for s in stories if s.persona_normalized != "unknown"})
        if personas:
            suggestions.append(
                list_related_entities(
                    "app", app.slug, "persona", personas
                ).model_dump()
            )

    # Check accelerator references
    accelerator_slugs = await ctx.get_accelerator_slugs()
    for acc_slug in app.accelerators:
        if acc_slug not in accelerator_slugs:
            suggestions.append(
                app_references_unknown_accelerator(
                    app.slug, acc_slug, list(accelerator_slugs)[:10]
                ).model_dump()
            )

    return suggestions


async def compute_persona_suggestions(
    persona: Persona, ctx: SuggestionContext
) -> list[dict]:
    """Compute suggestions for a persona."""
    from ....hcd_api.suggestions import (
        list_related_entities,
        persona_has_no_stories,
        persona_has_stories_but_no_journeys,
    )

    suggestions = []

    # Check if defined persona has no stories (reconciliation warning)
    if persona.is_defined and not persona.app_slugs:
        suggestions.append(
            persona_has_no_stories(persona.name, persona.slug).model_dump()
        )

    # Check if persona has journeys
    journeys = await ctx.get_journeys_for_persona(persona.name)
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
