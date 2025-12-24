"""Memory implementation of SuggestionContextService."""

from julee.hcd.entities.accelerator import Accelerator
from julee.hcd.entities.app import App
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.integration import Integration
from julee.hcd.entities.journey import Journey
from julee.hcd.entities.story import Story
from julee.hcd.repositories.accelerator import AcceleratorRepository
from julee.hcd.repositories.app import AppRepository
from julee.hcd.repositories.epic import EpicRepository
from julee.hcd.repositories.integration import IntegrationRepository
from julee.hcd.repositories.journey import JourneyRepository
from julee.hcd.repositories.story import StoryRepository
from julee.hcd.services.suggestion_context import SuggestionContextService
from julee.hcd.utils import normalize_name


class MemorySuggestionContextService(SuggestionContextService):
    """In-memory implementation of SuggestionContextService with caching.

    Provides cross-entity queries with request-scoped caching to avoid
    repeated repository calls during suggestion computation.
    """

    def __init__(
        self,
        story_repo: StoryRepository,
        epic_repo: EpicRepository,
        journey_repo: JourneyRepository,
        accelerator_repo: AcceleratorRepository,
        integration_repo: IntegrationRepository,
        app_repo: AppRepository,
    ) -> None:
        """Initialize with repository dependencies.

        Args:
            story_repo: Story repository instance
            epic_repo: Epic repository instance
            journey_repo: Journey repository instance
            accelerator_repo: Accelerator repository instance
            integration_repo: Integration repository instance
            app_repo: App repository instance
        """
        self.story_repo = story_repo
        self.epic_repo = epic_repo
        self.journey_repo = journey_repo
        self.accelerator_repo = accelerator_repo
        self.integration_repo = integration_repo
        self.app_repo = app_repo

        # Request-scoped caches
        self._stories: list[Story] | None = None
        self._epics: list[Epic] | None = None
        self._journeys: list[Journey] | None = None
        self._accelerators: list[Accelerator] | None = None
        self._integrations: list[Integration] | None = None
        self._apps: list[App] | None = None

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
        return {
            s.persona_normalized for s in stories if s.persona_normalized != "unknown"
        }

    async def get_epics_containing_story(self, story_title: str) -> list[Epic]:
        """Find epics that reference a story by title."""
        epics = await self.get_all_epics()
        normalized = normalize_name(story_title)
        return [
            e
            for e in epics
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

    async def get_accelerators_using_integration(
        self, integration_slug: str
    ) -> list[Accelerator]:
        """Find accelerators that source from or publish to an integration."""
        accelerators = await self.get_all_accelerators()
        return [
            a
            for a in accelerators
            if any(ref.slug == integration_slug for ref in a.sources_from)
            or any(ref.slug == integration_slug for ref in a.publishes_to)
        ]

    async def get_apps_using_accelerator(self, accelerator_slug: str) -> list[App]:
        """Find apps that reference an accelerator."""
        apps = await self.get_all_apps()
        return [a for a in apps if accelerator_slug in a.accelerators]
