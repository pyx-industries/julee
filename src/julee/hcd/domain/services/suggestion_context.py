"""SuggestionContextService protocol.

Defines the interface for cross-entity queries used in suggestion computation.
"""

from typing import Protocol, runtime_checkable

from julee.hcd.entities.accelerator import Accelerator
from julee.hcd.entities.app import App
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.integration import Integration
from julee.hcd.entities.journey import Journey
from julee.hcd.entities.story import Story

from ..use_cases.requests import (
    GetAcceleratorSlugsRequest,
    GetAcceleratorsUsingIntegrationRequest,
    GetAllAcceleratorsRequest,
    GetAllAppsRequest,
    GetAllEpicsRequest,
    GetAllIntegrationsRequest,
    GetAllJourneysRequest,
    GetAllStoriesRequest,
    GetAppSlugsRequest,
    GetAppsUsingAcceleratorRequest,
    GetEpicsContainingStoryRequest,
    GetEpicSlugsRequest,
    GetIntegrationSlugsRequest,
    GetJourneysForPersonaRequest,
    GetJourneySlugsRequest,
    GetPersonasRequest,
    GetStoriesForAppRequest,
    GetStorySlugsRequest,
    GetStoryTitlesNormalizedRequest,
)


@runtime_checkable
class SuggestionContextService(Protocol):
    """Service protocol for cross-entity suggestion queries.

    Provides methods for querying entities across repositories with
    caching support. Used by suggestion computation use cases to
    efficiently access related entities.
    """

    async def get_all_stories(self, request: GetAllStoriesRequest) -> list[Story]:
        """Get all stories.

        Args:
            request: Request object

        Returns:
            List of all stories
        """
        ...

    async def get_all_epics(self, request: GetAllEpicsRequest) -> list[Epic]:
        """Get all epics.

        Args:
            request: Request object

        Returns:
            List of all epics
        """
        ...

    async def get_all_journeys(self, request: GetAllJourneysRequest) -> list[Journey]:
        """Get all journeys.

        Args:
            request: Request object

        Returns:
            List of all journeys
        """
        ...

    async def get_all_accelerators(
        self, request: GetAllAcceleratorsRequest
    ) -> list[Accelerator]:
        """Get all accelerators.

        Args:
            request: Request object

        Returns:
            List of all accelerators
        """
        ...

    async def get_all_integrations(
        self, request: GetAllIntegrationsRequest
    ) -> list[Integration]:
        """Get all integrations.

        Args:
            request: Request object

        Returns:
            List of all integrations
        """
        ...

    async def get_all_apps(self, request: GetAllAppsRequest) -> list[App]:
        """Get all apps.

        Args:
            request: Request object

        Returns:
            List of all apps
        """
        ...

    async def get_story_slugs(self, request: GetStorySlugsRequest) -> set[str]:
        """Get set of all story slugs.

        Args:
            request: Request object

        Returns:
            Set of story slugs
        """
        ...

    async def get_story_titles_normalized(
        self, request: GetStoryTitlesNormalizedRequest
    ) -> dict[str, Story]:
        """Get mapping of normalized feature titles to stories.

        Args:
            request: Request object

        Returns:
            Dict mapping normalized title to Story
        """
        ...

    async def get_epic_slugs(self, request: GetEpicSlugsRequest) -> set[str]:
        """Get set of all epic slugs.

        Args:
            request: Request object

        Returns:
            Set of epic slugs
        """
        ...

    async def get_journey_slugs(self, request: GetJourneySlugsRequest) -> set[str]:
        """Get set of all journey slugs.

        Args:
            request: Request object

        Returns:
            Set of journey slugs
        """
        ...

    async def get_accelerator_slugs(
        self, request: GetAcceleratorSlugsRequest
    ) -> set[str]:
        """Get set of all accelerator slugs.

        Args:
            request: Request object

        Returns:
            Set of accelerator slugs
        """
        ...

    async def get_integration_slugs(
        self, request: GetIntegrationSlugsRequest
    ) -> set[str]:
        """Get set of all integration slugs.

        Args:
            request: Request object

        Returns:
            Set of integration slugs
        """
        ...

    async def get_app_slugs(self, request: GetAppSlugsRequest) -> set[str]:
        """Get set of all app slugs.

        Args:
            request: Request object

        Returns:
            Set of app slugs
        """
        ...

    async def get_personas(self, request: GetPersonasRequest) -> set[str]:
        """Get set of all unique personas from stories.

        Args:
            request: Request object

        Returns:
            Set of normalized persona names (excluding "unknown")
        """
        ...

    async def get_epics_containing_story(
        self, request: GetEpicsContainingStoryRequest
    ) -> list[Epic]:
        """Find epics that reference a story by title.

        Args:
            request: Contains story_title to search for

        Returns:
            List of epics containing the story reference
        """
        ...

    async def get_journeys_for_persona(
        self, request: GetJourneysForPersonaRequest
    ) -> list[Journey]:
        """Find journeys for a specific persona.

        Args:
            request: Contains persona name to search for

        Returns:
            List of journeys for the persona
        """
        ...

    async def get_stories_for_app(
        self, request: GetStoriesForAppRequest
    ) -> list[Story]:
        """Find stories belonging to an app.

        Args:
            request: Contains app_slug

        Returns:
            List of stories for the app
        """
        ...

    async def get_accelerators_using_integration(
        self, request: GetAcceleratorsUsingIntegrationRequest
    ) -> list[Accelerator]:
        """Find accelerators that source from or publish to an integration.

        Args:
            request: Contains integration_slug to search for

        Returns:
            List of accelerators using the integration
        """
        ...

    async def get_apps_using_accelerator(
        self, request: GetAppsUsingAcceleratorRequest
    ) -> list[App]:
        """Find apps that reference an accelerator.

        Args:
            request: Contains accelerator_slug to search for

        Returns:
            List of apps using the accelerator
        """
        ...
