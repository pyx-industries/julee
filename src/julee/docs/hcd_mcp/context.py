"""Repository and use-case context for MCP tools.

Provides repository instances and use-case factories for MCP tool functions.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..sphinx_hcd.domain.use_cases.suggestions import SuggestionContext

from ..sphinx_hcd.domain.use_cases import (
    # Accelerator use-cases
    CreateAcceleratorUseCase,
    # App use-cases
    CreateAppUseCase,
    # Epic use-cases
    CreateEpicUseCase,
    # Integration use-cases
    CreateIntegrationUseCase,
    # Journey use-cases
    CreateJourneyUseCase,
    # Persona use-cases
    CreatePersonaUseCase,
    # Story use-cases
    CreateStoryUseCase,
    DeleteAcceleratorUseCase,
    DeleteAppUseCase,
    DeleteEpicUseCase,
    DeleteIntegrationUseCase,
    DeleteJourneyUseCase,
    DeletePersonaUseCase,
    DeleteStoryUseCase,
    # Query use-cases
    DerivePersonasUseCase,
    GetAcceleratorUseCase,
    GetAppUseCase,
    GetEpicUseCase,
    GetIntegrationUseCase,
    GetJourneyUseCase,
    GetPersonaUseCase,
    GetStoryUseCase,
    ListAcceleratorsUseCase,
    ListAppsUseCase,
    ListEpicsUseCase,
    ListIntegrationsUseCase,
    ListJourneysUseCase,
    ListPersonasUseCase,
    ListStoriesUseCase,
    UpdateAcceleratorUseCase,
    UpdateAppUseCase,
    UpdateEpicUseCase,
    UpdateIntegrationUseCase,
    UpdateJourneyUseCase,
    UpdatePersonaUseCase,
    UpdateStoryUseCase,
)
from ..sphinx_hcd.repositories.file import (
    FileAcceleratorRepository,
    FileAppRepository,
    FileEpicRepository,
    FileIntegrationRepository,
    FileJourneyRepository,
    FileStoryRepository,
)
from ..sphinx_hcd.repositories.memory import MemoryPersonaRepository


def get_docs_root() -> Path:
    """Get the documentation root directory from environment.

    Returns:
        Path to the docs root directory
    """
    return Path(os.getenv("HCD_DOCS_ROOT", "docs"))


# =============================================================================
# Repository Factories
# =============================================================================


@lru_cache
def get_story_repository() -> FileStoryRepository:
    """Get the story repository singleton."""
    docs_root = get_docs_root()
    return FileStoryRepository(docs_root / "features")


@lru_cache
def get_epic_repository() -> FileEpicRepository:
    """Get the epic repository singleton."""
    docs_root = get_docs_root()
    return FileEpicRepository(docs_root / "epics")


@lru_cache
def get_journey_repository() -> FileJourneyRepository:
    """Get the journey repository singleton."""
    docs_root = get_docs_root()
    return FileJourneyRepository(docs_root / "journeys")


@lru_cache
def get_app_repository() -> FileAppRepository:
    """Get the app repository singleton."""
    docs_root = get_docs_root()
    return FileAppRepository(docs_root / "apps")


@lru_cache
def get_integration_repository() -> FileIntegrationRepository:
    """Get the integration repository singleton."""
    docs_root = get_docs_root()
    return FileIntegrationRepository(docs_root / "integrations")


@lru_cache
def get_accelerator_repository() -> FileAcceleratorRepository:
    """Get the accelerator repository singleton."""
    docs_root = get_docs_root()
    return FileAcceleratorRepository(docs_root / "accelerators")


@lru_cache
def get_persona_repository() -> MemoryPersonaRepository:
    """Get the persona repository singleton.

    Note: Uses memory repository as personas are primarily defined
    via Sphinx directives or MCP tools, not persisted to files yet.
    """
    return MemoryPersonaRepository()


# =============================================================================
# Story Use-Case Factories
# =============================================================================


def get_create_story_use_case() -> CreateStoryUseCase:
    """Get CreateStoryUseCase with repository dependency."""
    return CreateStoryUseCase(get_story_repository())


def get_get_story_use_case() -> GetStoryUseCase:
    """Get GetStoryUseCase with repository dependency."""
    return GetStoryUseCase(get_story_repository())


def get_list_stories_use_case() -> ListStoriesUseCase:
    """Get ListStoriesUseCase with repository dependency."""
    return ListStoriesUseCase(get_story_repository())


def get_update_story_use_case() -> UpdateStoryUseCase:
    """Get UpdateStoryUseCase with repository dependency."""
    return UpdateStoryUseCase(get_story_repository())


def get_delete_story_use_case() -> DeleteStoryUseCase:
    """Get DeleteStoryUseCase with repository dependency."""
    return DeleteStoryUseCase(get_story_repository())


# =============================================================================
# Epic Use-Case Factories
# =============================================================================


def get_create_epic_use_case() -> CreateEpicUseCase:
    """Get CreateEpicUseCase with repository dependency."""
    return CreateEpicUseCase(get_epic_repository())


def get_get_epic_use_case() -> GetEpicUseCase:
    """Get GetEpicUseCase with repository dependency."""
    return GetEpicUseCase(get_epic_repository())


def get_list_epics_use_case() -> ListEpicsUseCase:
    """Get ListEpicsUseCase with repository dependency."""
    return ListEpicsUseCase(get_epic_repository())


def get_update_epic_use_case() -> UpdateEpicUseCase:
    """Get UpdateEpicUseCase with repository dependency."""
    return UpdateEpicUseCase(get_epic_repository())


def get_delete_epic_use_case() -> DeleteEpicUseCase:
    """Get DeleteEpicUseCase with repository dependency."""
    return DeleteEpicUseCase(get_epic_repository())


# =============================================================================
# Journey Use-Case Factories
# =============================================================================


def get_create_journey_use_case() -> CreateJourneyUseCase:
    """Get CreateJourneyUseCase with repository dependency."""
    return CreateJourneyUseCase(get_journey_repository())


def get_get_journey_use_case() -> GetJourneyUseCase:
    """Get GetJourneyUseCase with repository dependency."""
    return GetJourneyUseCase(get_journey_repository())


def get_list_journeys_use_case() -> ListJourneysUseCase:
    """Get ListJourneysUseCase with repository dependency."""
    return ListJourneysUseCase(get_journey_repository())


def get_update_journey_use_case() -> UpdateJourneyUseCase:
    """Get UpdateJourneyUseCase with repository dependency."""
    return UpdateJourneyUseCase(get_journey_repository())


def get_delete_journey_use_case() -> DeleteJourneyUseCase:
    """Get DeleteJourneyUseCase with repository dependency."""
    return DeleteJourneyUseCase(get_journey_repository())


# =============================================================================
# Accelerator Use-Case Factories
# =============================================================================


def get_create_accelerator_use_case() -> CreateAcceleratorUseCase:
    """Get CreateAcceleratorUseCase with repository dependency."""
    return CreateAcceleratorUseCase(get_accelerator_repository())


def get_get_accelerator_use_case() -> GetAcceleratorUseCase:
    """Get GetAcceleratorUseCase with repository dependency."""
    return GetAcceleratorUseCase(get_accelerator_repository())


def get_list_accelerators_use_case() -> ListAcceleratorsUseCase:
    """Get ListAcceleratorsUseCase with repository dependency."""
    return ListAcceleratorsUseCase(get_accelerator_repository())


def get_update_accelerator_use_case() -> UpdateAcceleratorUseCase:
    """Get UpdateAcceleratorUseCase with repository dependency."""
    return UpdateAcceleratorUseCase(get_accelerator_repository())


def get_delete_accelerator_use_case() -> DeleteAcceleratorUseCase:
    """Get DeleteAcceleratorUseCase with repository dependency."""
    return DeleteAcceleratorUseCase(get_accelerator_repository())


# =============================================================================
# Integration Use-Case Factories
# =============================================================================


def get_create_integration_use_case() -> CreateIntegrationUseCase:
    """Get CreateIntegrationUseCase with repository dependency."""
    return CreateIntegrationUseCase(get_integration_repository())


def get_get_integration_use_case() -> GetIntegrationUseCase:
    """Get GetIntegrationUseCase with repository dependency."""
    return GetIntegrationUseCase(get_integration_repository())


def get_list_integrations_use_case() -> ListIntegrationsUseCase:
    """Get ListIntegrationsUseCase with repository dependency."""
    return ListIntegrationsUseCase(get_integration_repository())


def get_update_integration_use_case() -> UpdateIntegrationUseCase:
    """Get UpdateIntegrationUseCase with repository dependency."""
    return UpdateIntegrationUseCase(get_integration_repository())


def get_delete_integration_use_case() -> DeleteIntegrationUseCase:
    """Get DeleteIntegrationUseCase with repository dependency."""
    return DeleteIntegrationUseCase(get_integration_repository())


# =============================================================================
# App Use-Case Factories
# =============================================================================


def get_create_app_use_case() -> CreateAppUseCase:
    """Get CreateAppUseCase with repository dependency."""
    return CreateAppUseCase(get_app_repository())


def get_get_app_use_case() -> GetAppUseCase:
    """Get GetAppUseCase with repository dependency."""
    return GetAppUseCase(get_app_repository())


def get_list_apps_use_case() -> ListAppsUseCase:
    """Get ListAppsUseCase with repository dependency."""
    return ListAppsUseCase(get_app_repository())


def get_update_app_use_case() -> UpdateAppUseCase:
    """Get UpdateAppUseCase with repository dependency."""
    return UpdateAppUseCase(get_app_repository())


def get_delete_app_use_case() -> DeleteAppUseCase:
    """Get DeleteAppUseCase with repository dependency."""
    return DeleteAppUseCase(get_app_repository())


# =============================================================================
# Persona Use-Case Factories
# =============================================================================


def get_create_persona_use_case() -> CreatePersonaUseCase:
    """Get CreatePersonaUseCase with repository dependency."""
    return CreatePersonaUseCase(get_persona_repository())


def get_list_personas_use_case() -> ListPersonasUseCase:
    """Get ListPersonasUseCase with repository dependency."""
    return ListPersonasUseCase(get_persona_repository())


def get_update_persona_use_case() -> UpdatePersonaUseCase:
    """Get UpdatePersonaUseCase with repository dependency."""
    return UpdatePersonaUseCase(get_persona_repository())


def get_delete_persona_use_case() -> DeletePersonaUseCase:
    """Get DeletePersonaUseCase with repository dependency."""
    return DeletePersonaUseCase(get_persona_repository())


# =============================================================================
# Query Use-Case Factories
# =============================================================================


def get_derive_personas_use_case() -> DerivePersonasUseCase:
    """Get DerivePersonasUseCase with repository dependencies."""
    return DerivePersonasUseCase(
        story_repo=get_story_repository(),
        epic_repo=get_epic_repository(),
        persona_repo=get_persona_repository(),
    )


def get_get_persona_use_case() -> GetPersonaUseCase:
    """Get GetPersonaUseCase with repository dependencies."""
    return GetPersonaUseCase(
        story_repo=get_story_repository(),
        epic_repo=get_epic_repository(),
        persona_repo=get_persona_repository(),
    )


# =============================================================================
# Suggestion Context Factory
# =============================================================================


def get_suggestion_context() -> "SuggestionContext":
    """Get SuggestionContext with all repository dependencies.

    This provides the cross-entity visibility needed to compute
    contextual suggestions based on domain relationships.
    """
    from ..sphinx_hcd.domain.use_cases.suggestions import SuggestionContext

    return SuggestionContext(
        story_repo=get_story_repository(),
        epic_repo=get_epic_repository(),
        journey_repo=get_journey_repository(),
        accelerator_repo=get_accelerator_repository(),
        integration_repo=get_integration_repository(),
        app_repo=get_app_repository(),
        persona_repo=get_persona_repository(),
    )
