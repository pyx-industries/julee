"""CRUD use cases for HCD entities.

Generic CRUD operations using base classes from julee.core.use_cases.generic_crud.
Domain-specific queries (get_by_persona, etc.) remain in dedicated use case modules.
"""

from julee.core.use_cases import generic_crud
from julee.hcd.entities.accelerator import Accelerator
from julee.hcd.entities.app import App
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.integration import Integration
from julee.hcd.entities.journey import Journey
from julee.hcd.entities.persona import Persona
from julee.hcd.entities.story import Story
from julee.hcd.repositories.accelerator import AcceleratorRepository
from julee.hcd.repositories.app import AppRepository
from julee.hcd.repositories.epic import EpicRepository
from julee.hcd.repositories.integration import IntegrationRepository
from julee.hcd.repositories.journey import JourneyRepository
from julee.hcd.repositories.persona import PersonaRepository
from julee.hcd.repositories.story import StoryRepository

# =============================================================================
# Story
# =============================================================================


class GetStoryRequest(generic_crud.GetRequest):
    """Get story by slug."""


class GetStoryResponse(generic_crud.GetResponse[Story]):
    """Story get response."""


class GetStoryUseCase(generic_crud.GetUseCase[Story, StoryRepository]):
    """Get a story by slug."""


class ListStoriesRequest(generic_crud.ListRequest):
    """List all stories."""


class ListStoriesResponse(generic_crud.ListResponse[Story]):
    """Stories list response."""


class ListStoriesUseCase(generic_crud.ListUseCase[Story, StoryRepository]):
    """List all stories."""


class DeleteStoryRequest(generic_crud.DeleteRequest):
    """Delete story by slug."""


class DeleteStoryResponse(generic_crud.DeleteResponse):
    """Story delete response."""


class DeleteStoryUseCase(generic_crud.DeleteUseCase[Story, StoryRepository]):
    """Delete a story by slug."""


class CreateStoryRequest(generic_crud.CreateRequest):
    """Create a story. Slug auto-generated from app_slug + feature_title."""

    feature_title: str
    persona: str
    app_slug: str
    i_want: str = "do something"
    so_that: str = "achieve a goal"
    file_path: str = ""
    abs_path: str = ""
    gherkin_snippet: str = ""


class CreateStoryResponse(generic_crud.CreateResponse[Story]):
    """Story create response."""


class CreateStoryUseCase(generic_crud.CreateUseCase[Story, StoryRepository]):
    """Create a story."""

    entity_cls = Story


# =============================================================================
# Epic
# =============================================================================


class GetEpicRequest(generic_crud.GetRequest):
    """Get epic by slug."""


class GetEpicResponse(generic_crud.GetResponse[Epic]):
    """Epic get response."""


class GetEpicUseCase(generic_crud.GetUseCase[Epic, EpicRepository]):
    """Get an epic by slug."""


class ListEpicsRequest(generic_crud.ListRequest):
    """List all epics."""


class ListEpicsResponse(generic_crud.ListResponse[Epic]):
    """Epics list response."""


class ListEpicsUseCase(generic_crud.ListUseCase[Epic, EpicRepository]):
    """List all epics."""


class DeleteEpicRequest(generic_crud.DeleteRequest):
    """Delete epic by slug."""


class DeleteEpicResponse(generic_crud.DeleteResponse):
    """Epic delete response."""


class DeleteEpicUseCase(generic_crud.DeleteUseCase[Epic, EpicRepository]):
    """Delete an epic by slug."""


# =============================================================================
# Persona
# =============================================================================


class GetPersonaRequest(generic_crud.GetRequest):
    """Get persona by slug."""


class GetPersonaResponse(generic_crud.GetResponse[Persona]):
    """Persona get response."""


class GetPersonaUseCase(generic_crud.GetUseCase[Persona, PersonaRepository]):
    """Get a persona by slug."""


class ListPersonasRequest(generic_crud.ListRequest):
    """List all personas."""


class ListPersonasResponse(generic_crud.ListResponse[Persona]):
    """Personas list response."""


class ListPersonasUseCase(generic_crud.ListUseCase[Persona, PersonaRepository]):
    """List all personas."""


class DeletePersonaRequest(generic_crud.DeleteRequest):
    """Delete persona by slug."""


class DeletePersonaResponse(generic_crud.DeleteResponse):
    """Persona delete response."""


class DeletePersonaUseCase(generic_crud.DeleteUseCase[Persona, PersonaRepository]):
    """Delete a persona by slug."""


# =============================================================================
# Journey
# =============================================================================


class GetJourneyRequest(generic_crud.GetRequest):
    """Get journey by slug."""


class GetJourneyResponse(generic_crud.GetResponse[Journey]):
    """Journey get response."""


class GetJourneyUseCase(generic_crud.GetUseCase[Journey, JourneyRepository]):
    """Get a journey by slug."""


class ListJourneysRequest(generic_crud.ListRequest):
    """List all journeys."""


class ListJourneysResponse(generic_crud.ListResponse[Journey]):
    """Journeys list response."""


class ListJourneysUseCase(generic_crud.ListUseCase[Journey, JourneyRepository]):
    """List all journeys."""


class DeleteJourneyRequest(generic_crud.DeleteRequest):
    """Delete journey by slug."""


class DeleteJourneyResponse(generic_crud.DeleteResponse):
    """Journey delete response."""


class DeleteJourneyUseCase(generic_crud.DeleteUseCase[Journey, JourneyRepository]):
    """Delete a journey by slug."""


# =============================================================================
# App
# =============================================================================


class GetAppRequest(generic_crud.GetRequest):
    """Get app by slug."""


class GetAppResponse(generic_crud.GetResponse[App]):
    """App get response."""


class GetAppUseCase(generic_crud.GetUseCase[App, AppRepository]):
    """Get an app by slug."""


class ListAppsRequest(generic_crud.ListRequest):
    """List all apps."""


class ListAppsResponse(generic_crud.ListResponse[App]):
    """Apps list response."""


class ListAppsUseCase(generic_crud.ListUseCase[App, AppRepository]):
    """List all apps."""


class DeleteAppRequest(generic_crud.DeleteRequest):
    """Delete app by slug."""


class DeleteAppResponse(generic_crud.DeleteResponse):
    """App delete response."""


class DeleteAppUseCase(generic_crud.DeleteUseCase[App, AppRepository]):
    """Delete an app by slug."""


# =============================================================================
# Accelerator
# =============================================================================


class GetAcceleratorRequest(generic_crud.GetRequest):
    """Get accelerator by slug."""


class GetAcceleratorResponse(generic_crud.GetResponse[Accelerator]):
    """Accelerator get response."""


class GetAcceleratorUseCase(
    generic_crud.GetUseCase[Accelerator, AcceleratorRepository]
):
    """Get an accelerator by slug."""


class ListAcceleratorsRequest(generic_crud.ListRequest):
    """List all accelerators."""


class ListAcceleratorsResponse(generic_crud.ListResponse[Accelerator]):
    """Accelerators list response."""


class ListAcceleratorsUseCase(
    generic_crud.ListUseCase[Accelerator, AcceleratorRepository]
):
    """List all accelerators."""


class DeleteAcceleratorRequest(generic_crud.DeleteRequest):
    """Delete accelerator by slug."""


class DeleteAcceleratorResponse(generic_crud.DeleteResponse):
    """Accelerator delete response."""


class DeleteAcceleratorUseCase(
    generic_crud.DeleteUseCase[Accelerator, AcceleratorRepository]
):
    """Delete an accelerator by slug."""


# =============================================================================
# Integration
# =============================================================================


class GetIntegrationRequest(generic_crud.GetRequest):
    """Get integration by slug."""


class GetIntegrationResponse(generic_crud.GetResponse[Integration]):
    """Integration get response."""


class GetIntegrationUseCase(
    generic_crud.GetUseCase[Integration, IntegrationRepository]
):
    """Get an integration by slug."""


class ListIntegrationsRequest(generic_crud.ListRequest):
    """List all integrations."""


class ListIntegrationsResponse(generic_crud.ListResponse[Integration]):
    """Integrations list response."""


class ListIntegrationsUseCase(
    generic_crud.ListUseCase[Integration, IntegrationRepository]
):
    """List all integrations."""


class DeleteIntegrationRequest(generic_crud.DeleteRequest):
    """Delete integration by slug."""


class DeleteIntegrationResponse(generic_crud.DeleteResponse):
    """Integration delete response."""


class DeleteIntegrationUseCase(
    generic_crud.DeleteUseCase[Integration, IntegrationRepository]
):
    """Delete an integration by slug."""
