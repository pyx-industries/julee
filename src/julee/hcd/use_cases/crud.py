"""CRUD use cases for HCD entities.

Generic CRUD operations using base classes from julee.core.use_cases.generic_crud.
Domain-specific queries (get_by_persona, etc.) remain in dedicated use case modules.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from julee.core.use_cases import generic_crud
from julee.hcd.entities.accelerator import Accelerator
from julee.hcd.entities.app import App, AppType
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

    response_cls = GetStoryResponse


class ListStoriesRequest(generic_crud.ListRequest):
    """List stories with optional filters."""

    app_slug: str | None = Field(default=None, description="Filter by app slug")
    persona: str | None = Field(default=None, description="Filter by persona name")


class ListStoriesResponse(generic_crud.ListResponse[Story]):
    """Stories list response."""

    def grouped_by_persona(self) -> dict[str, list[Story]]:
        """Group stories by persona."""
        result: dict[str, list[Story]] = {}
        for story in self.entities:
            result.setdefault(story.persona, []).append(story)
        return result

    def grouped_by_app(self) -> dict[str, list[Story]]:
        """Group stories by app slug."""
        result: dict[str, list[Story]] = {}
        for story in self.entities:
            result.setdefault(story.app_slug, []).append(story)
        return result


class ListStoriesUseCase(generic_crud.FilterableListUseCase[Story, StoryRepository]):
    """List stories with optional filters."""

    response_cls = ListStoriesResponse


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
    response_cls = CreateStoryResponse


class UpdateStoryRequest(generic_crud.UpdateRequest):
    """Update story fields."""

    feature_title: str | None = None
    persona: str | None = None
    i_want: str | None = None
    so_that: str | None = None
    gherkin_snippet: str | None = None


class UpdateStoryResponse(generic_crud.UpdateResponse[Story]):
    """Story update response."""


class UpdateStoryUseCase(generic_crud.UpdateUseCase[Story, StoryRepository]):
    """Update a story."""

    response_cls = UpdateStoryResponse


# =============================================================================
# Epic
# =============================================================================


class GetEpicRequest(generic_crud.GetRequest):
    """Get epic by slug."""


class GetEpicResponse(generic_crud.GetResponse[Epic]):
    """Epic get response."""


class GetEpicUseCase(generic_crud.GetUseCase[Epic, EpicRepository]):
    """Get an epic by slug."""

    response_cls = GetEpicResponse


class ListEpicsRequest(generic_crud.ListRequest):
    """List epics with optional filters."""

    has_stories: bool | None = Field(
        default=None, description="Filter to epics with/without stories"
    )
    contains_story: str | None = Field(
        default=None, description="Filter to epics containing this story"
    )


class ListEpicsResponse(generic_crud.ListResponse[Epic]):
    """Epics list response."""

    @property
    def total_stories(self) -> int:
        """Total number of stories across all epics."""
        return sum(len(epic.story_refs) for epic in self.entities)


class ListEpicsUseCase(generic_crud.FilterableListUseCase[Epic, EpicRepository]):
    """List epics with optional filters."""

    response_cls = ListEpicsResponse


class DeleteEpicRequest(generic_crud.DeleteRequest):
    """Delete epic by slug."""


class DeleteEpicResponse(generic_crud.DeleteResponse):
    """Epic delete response."""


class DeleteEpicUseCase(generic_crud.DeleteUseCase[Epic, EpicRepository]):
    """Delete an epic by slug."""


class CreateEpicRequest(BaseModel):
    """Request for creating an epic."""

    slug: str = Field(description="URL-safe identifier")
    description: str = Field(default="", description="Epic description")
    story_refs: list[str] = Field(
        default_factory=list, description="Story feature titles"
    )
    docname: str = Field(default="", description="RST document where defined")


class CreateEpicResponse(generic_crud.CreateResponse[Epic]):
    """Epic create response."""


class CreateEpicUseCase(generic_crud.CreateUseCase[Epic, EpicRepository]):
    """Create an epic."""

    entity_cls = Epic
    response_cls = CreateEpicResponse


class UpdateEpicRequest(generic_crud.UpdateRequest):
    """Update epic fields."""

    description: str | None = None
    story_refs: list[str] | None = None


class UpdateEpicResponse(generic_crud.UpdateResponse[Epic]):
    """Epic update response."""


class UpdateEpicUseCase(generic_crud.UpdateUseCase[Epic, EpicRepository]):
    """Update an epic."""

    response_cls = UpdateEpicResponse


# =============================================================================
# Persona
# =============================================================================


class GetPersonaRequest(generic_crud.GetRequest):
    """Get persona by slug."""


class GetPersonaResponse(generic_crud.GetResponse[Persona]):
    """Persona get response."""


class GetPersonaUseCase(generic_crud.GetUseCase[Persona, PersonaRepository]):
    """Get a persona by slug."""

    response_cls = GetPersonaResponse


# Backward compatibility aliases (tests use GetPersonaBySlug* names)
GetPersonaBySlugRequest = GetPersonaRequest
GetPersonaBySlugResponse = GetPersonaResponse
GetPersonaBySlugUseCase = GetPersonaUseCase


class ListPersonasRequest(generic_crud.ListRequest):
    """List all personas."""


class ListPersonasResponse(generic_crud.ListResponse[Persona]):
    """Personas list response."""


class ListPersonasUseCase(generic_crud.ListUseCase[Persona, PersonaRepository]):
    """List all personas."""

    response_cls = ListPersonasResponse


class DeletePersonaRequest(generic_crud.DeleteRequest):
    """Delete persona by slug."""


class DeletePersonaResponse(generic_crud.DeleteResponse):
    """Persona delete response."""


class DeletePersonaUseCase(generic_crud.DeleteUseCase[Persona, PersonaRepository]):
    """Delete a persona by slug."""


class CreatePersonaRequest(BaseModel):
    """Request for creating a persona."""

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name (used in Gherkin 'As a {name}')")
    goals: list[str] = Field(default_factory=list, description="What the persona wants")
    frustrations: list[str] = Field(default_factory=list, description="Pain points")
    jobs_to_be_done: list[str] = Field(default_factory=list, description="JTBD items")
    context: str = Field(default="", description="Background and situational context")
    app_slugs: list[str] = Field(
        default_factory=list, description="Apps this persona uses"
    )
    accelerator_slugs: list[str] = Field(
        default_factory=list, description="Accelerators used"
    )
    contrib_slugs: list[str] = Field(
        default_factory=list, description="Contrib modules used"
    )
    docname: str = Field(default="", description="RST document where defined")


class CreatePersonaResponse(generic_crud.CreateResponse[Persona]):
    """Persona create response."""


class CreatePersonaUseCase(generic_crud.CreateUseCase[Persona, PersonaRepository]):
    """Create a persona."""

    entity_cls = Persona
    response_cls = CreatePersonaResponse


class UpdatePersonaRequest(generic_crud.UpdateRequest):
    """Update persona fields."""

    name: str | None = None
    goals: list[str] | None = None
    frustrations: list[str] | None = None
    jobs_to_be_done: list[str] | None = None
    context: str | None = None
    app_slugs: list[str] | None = None
    accelerator_slugs: list[str] | None = None
    contrib_slugs: list[str] | None = None


class UpdatePersonaResponse(generic_crud.UpdateResponse[Persona]):
    """Persona update response."""


class UpdatePersonaUseCase(generic_crud.UpdateUseCase[Persona, PersonaRepository]):
    """Update a persona."""

    response_cls = UpdatePersonaResponse


# =============================================================================
# Journey
# =============================================================================


class GetJourneyRequest(generic_crud.GetRequest):
    """Get journey by slug."""


class GetJourneyResponse(generic_crud.GetResponse[Journey]):
    """Journey get response."""


class GetJourneyUseCase(generic_crud.GetUseCase[Journey, JourneyRepository]):
    """Get a journey by slug."""

    response_cls = GetJourneyResponse


class ListJourneysRequest(generic_crud.ListRequest):
    """List journeys with optional filters."""

    contains_story: str | None = Field(
        default=None, description="Filter to journeys containing this story"
    )


class ListJourneysResponse(generic_crud.ListResponse[Journey]):
    """Journeys list response."""


class ListJourneysUseCase(
    generic_crud.FilterableListUseCase[Journey, JourneyRepository]
):
    """List journeys with optional filters."""

    response_cls = ListJourneysResponse


class DeleteJourneyRequest(generic_crud.DeleteRequest):
    """Delete journey by slug."""


class DeleteJourneyResponse(generic_crud.DeleteResponse):
    """Journey delete response."""


class DeleteJourneyUseCase(generic_crud.DeleteUseCase[Journey, JourneyRepository]):
    """Delete a journey by slug."""


class CreateJourneyRequest(BaseModel):
    """Request for creating a journey.

    Steps should be provided as dicts with step_type, ref, and optional description.
    The entity's from_create_data() handles conversion to JourneyStep objects.
    """

    slug: str = Field(description="URL-safe identifier")
    persona: str = Field(default="", description="Persona undertaking this journey")
    intent: str = Field(default="", description="What the persona wants")
    outcome: str = Field(default="", description="What success looks like")
    goal: str = Field(default="", description="Activity description")
    depends_on: list[str] = Field(
        default_factory=list, description="Journey dependencies"
    )
    steps: list[dict[str, Any]] = Field(
        default_factory=list, description="Journey steps"
    )
    preconditions: list[str] = Field(default_factory=list, description="Preconditions")
    postconditions: list[str] = Field(
        default_factory=list, description="Postconditions"
    )
    docname: str = Field(default="", description="RST document where defined")


class CreateJourneyResponse(generic_crud.CreateResponse[Journey]):
    """Journey create response."""


class CreateJourneyUseCase(generic_crud.CreateUseCase[Journey, JourneyRepository]):
    """Create a journey."""

    entity_cls = Journey
    response_cls = CreateJourneyResponse


class UpdateJourneyRequest(generic_crud.UpdateRequest):
    """Update journey fields."""

    persona: str | None = None
    intent: str | None = None
    outcome: str | None = None
    goal: str | None = None
    depends_on: list[str] | None = None
    steps: list[dict[str, Any]] | None = None
    preconditions: list[str] | None = None
    postconditions: list[str] | None = None


class UpdateJourneyResponse(generic_crud.UpdateResponse[Journey]):
    """Journey update response."""


class UpdateJourneyUseCase(generic_crud.UpdateUseCase[Journey, JourneyRepository]):
    """Update a journey."""

    response_cls = UpdateJourneyResponse


# =============================================================================
# App
# =============================================================================


class GetAppRequest(generic_crud.GetRequest):
    """Get app by slug."""


class GetAppResponse(generic_crud.GetResponse[App]):
    """App get response."""


class GetAppUseCase(generic_crud.GetUseCase[App, AppRepository]):
    """Get an app by slug."""

    response_cls = GetAppResponse


class ListAppsRequest(generic_crud.ListRequest):
    """List apps with optional filters."""

    app_type: str | None = Field(default=None, description="Filter by app type")
    has_accelerator: str | None = Field(
        default=None, description="Filter by accelerator slug"
    )


class ListAppsResponse(generic_crud.ListResponse[App]):
    """Apps list response."""

    def grouped_by_type(self) -> dict[str, list[App]]:
        """Group apps by app type."""
        result: dict[str, list[App]] = {}
        for app in self.entities:
            type_key = app.app_type.value if app.app_type else "unknown"
            result.setdefault(type_key, []).append(app)
        return result


class ListAppsUseCase(generic_crud.FilterableListUseCase[App, AppRepository]):
    """List apps with optional filters."""

    response_cls = ListAppsResponse


class DeleteAppRequest(generic_crud.DeleteRequest):
    """Delete app by slug."""


class DeleteAppResponse(generic_crud.DeleteResponse):
    """App delete response."""


class DeleteAppUseCase(generic_crud.DeleteUseCase[App, AppRepository]):
    """Delete an app by slug."""


class CreateAppRequest(BaseModel):
    """Request for creating an app.

    Accepts string values for enums (e.g., app_type="staff") which are
    coerced to proper enum types.
    """

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    app_type: AppType = Field(default=AppType.UNKNOWN, description="App classification")
    status: str | None = Field(default=None, description="Status indicator")
    description: str = Field(default="", description="Human-readable description")
    accelerators: list[str] = Field(
        default_factory=list, description="Accelerator slugs"
    )

    @field_validator("app_type", mode="before")
    @classmethod
    def coerce_app_type(cls, v):
        """Coerce string to AppType enum."""
        if isinstance(v, str):
            return AppType.from_string(v)
        return v


class CreateAppResponse(generic_crud.CreateResponse[App]):
    """App create response."""


class CreateAppUseCase(generic_crud.CreateUseCase[App, AppRepository]):
    """Create an app."""

    entity_cls = App
    response_cls = CreateAppResponse


class UpdateAppRequest(generic_crud.UpdateRequest):
    """Update app fields.

    Accepts string values for enums which are coerced to proper types.
    """

    name: str | None = None
    app_type: AppType | None = None
    status: str | None = None
    description: str | None = None
    accelerators: list[str] | None = None

    @field_validator("app_type", mode="before")
    @classmethod
    def coerce_app_type(cls, v):
        """Coerce string to AppType enum."""
        if v is None:
            return None
        if isinstance(v, str):
            return AppType.from_string(v)
        return v


class UpdateAppResponse(generic_crud.UpdateResponse[App]):
    """App update response."""


class UpdateAppUseCase(generic_crud.UpdateUseCase[App, AppRepository]):
    """Update an app."""

    response_cls = UpdateAppResponse


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

    response_cls = GetAcceleratorResponse


class ListAcceleratorsRequest(generic_crud.ListRequest):
    """List accelerators with optional filters."""

    status: str | None = Field(default=None, description="Filter by status")


class ListAcceleratorsResponse(generic_crud.ListResponse[Accelerator]):
    """Accelerators list response."""


class ListAcceleratorsUseCase(
    generic_crud.FilterableListUseCase[Accelerator, AcceleratorRepository]
):
    """List accelerators with optional filters."""

    response_cls = ListAcceleratorsResponse


class DeleteAcceleratorRequest(generic_crud.DeleteRequest):
    """Delete accelerator by slug."""


class DeleteAcceleratorResponse(generic_crud.DeleteResponse):
    """Accelerator delete response."""


class DeleteAcceleratorUseCase(
    generic_crud.DeleteUseCase[Accelerator, AcceleratorRepository]
):
    """Delete an accelerator by slug."""


class CreateAcceleratorRequest(BaseModel):
    """Request for creating an accelerator.

    sources_from and publishes_to should be provided as dicts with slug and description.
    The entity's from_create_data() handles conversion to IntegrationReference objects.
    """

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(default="", description="Display name")
    status: str = Field(default="", description="Development status")
    milestone: str | None = Field(default=None, description="Target milestone")
    acceptance: str | None = Field(default=None, description="Acceptance criteria")
    objective: str = Field(default="", description="Business objective")
    domain_concepts: list[str] = Field(
        default_factory=list, description="Domain concepts"
    )
    bounded_context_path: str = Field(default="", description="Source code path")
    technology: str = Field(default="Python", description="Technology stack")
    sources_from: list[dict[str, Any]] = Field(
        default_factory=list, description="Integration sources"
    )
    feeds_into: list[str] = Field(
        default_factory=list, description="Downstream accelerators"
    )
    publishes_to: list[dict[str, Any]] = Field(
        default_factory=list, description="Integration targets"
    )
    depends_on: list[str] = Field(
        default_factory=list, description="Upstream accelerators"
    )
    docname: str = Field(default="", description="RST document where defined")


class CreateAcceleratorResponse(generic_crud.CreateResponse[Accelerator]):
    """Accelerator create response."""


class CreateAcceleratorUseCase(
    generic_crud.CreateUseCase[Accelerator, AcceleratorRepository]
):
    """Create an accelerator."""

    entity_cls = Accelerator
    response_cls = CreateAcceleratorResponse


class UpdateAcceleratorRequest(generic_crud.UpdateRequest):
    """Update accelerator fields."""

    name: str | None = None
    status: str | None = None
    milestone: str | None = None
    acceptance: str | None = None
    objective: str | None = None
    domain_concepts: list[str] | None = None
    bounded_context_path: str | None = None
    technology: str | None = None
    sources_from: list[dict[str, Any]] | None = None
    feeds_into: list[str] | None = None
    publishes_to: list[dict[str, Any]] | None = None
    depends_on: list[str] | None = None


class UpdateAcceleratorResponse(generic_crud.UpdateResponse[Accelerator]):
    """Accelerator update response."""


class UpdateAcceleratorUseCase(
    generic_crud.UpdateUseCase[Accelerator, AcceleratorRepository]
):
    """Update an accelerator."""

    response_cls = UpdateAcceleratorResponse


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

    response_cls = GetIntegrationResponse


class ListIntegrationsRequest(generic_crud.ListRequest):
    """List all integrations."""


class ListIntegrationsResponse(generic_crud.ListResponse[Integration]):
    """Integrations list response."""


class ListIntegrationsUseCase(
    generic_crud.ListUseCase[Integration, IntegrationRepository]
):
    """List all integrations."""

    response_cls = ListIntegrationsResponse


class DeleteIntegrationRequest(generic_crud.DeleteRequest):
    """Delete integration by slug."""


class DeleteIntegrationResponse(generic_crud.DeleteResponse):
    """Integration delete response."""


class DeleteIntegrationUseCase(
    generic_crud.DeleteUseCase[Integration, IntegrationRepository]
):
    """Delete an integration by slug."""


class CreateIntegrationRequest(BaseModel):
    """Request for creating an integration.

    direction should be a string (inbound, outbound, bidirectional).
    depends_on should be provided as dicts with name, url, description.
    The entity's from_create_data() handles conversion.
    """

    slug: str = Field(description="URL-safe identifier")
    module: str = Field(description="Python module name")
    name: str = Field(description="Display name")
    description: str = Field(default="", description="Human-readable description")
    direction: str = Field(default="bidirectional", description="Data flow direction")
    depends_on: list[dict[str, Any]] = Field(
        default_factory=list, description="External dependencies"
    )


class CreateIntegrationResponse(generic_crud.CreateResponse[Integration]):
    """Integration create response."""


class CreateIntegrationUseCase(
    generic_crud.CreateUseCase[Integration, IntegrationRepository]
):
    """Create an integration."""

    entity_cls = Integration
    response_cls = CreateIntegrationResponse


class UpdateIntegrationRequest(generic_crud.UpdateRequest):
    """Update integration fields."""

    module: str | None = None
    name: str | None = None
    description: str | None = None
    direction: str | None = None
    depends_on: list[dict[str, Any]] | None = None


class UpdateIntegrationResponse(generic_crud.UpdateResponse[Integration]):
    """Integration update response."""


class UpdateIntegrationUseCase(
    generic_crud.UpdateUseCase[Integration, IntegrationRepository]
):
    """Update an integration."""

    response_cls = UpdateIntegrationResponse
